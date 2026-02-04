from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from tfm_ingestor.config import load_defaults, load_rules
from tfm_ingestor.mapping import build_governance_spec, merge_tag_fqns
from tfm_ingestor.om_api import OpenMetadataApi, OpenMetadataApiError, OmRef


def _tag_labels(tag_fqns: list[str]) -> list[dict[str, Any]]:
    # OpenMetadata TagLabel (simplified)
    return [{"tagFQN": fqn, "labelType": "Manual", "state": "Confirmed"} for fqn in tag_fqns]


def _existing_tag_fqns(table: dict[str, Any]) -> list[str]:
    tags = table.get("tags") or []
    out: list[str] = []
    for t in tags:
        if isinstance(t, dict) and t.get("tagFQN"):
            out.append(str(t["tagFQN"]))
    return out


def _existing_custom_properties(table: dict[str, Any]) -> dict[str, str]:
    ext = table.get("extension") or {}
    if not isinstance(ext, dict):
        return {}
    cp = ext.get("customProperties") or {}
    if not isinstance(cp, dict):
        return {}
    # Keep only scalar values for the PoC
    out: dict[str, str] = {}
    for k, v in cp.items():
        if v is None:
            continue
        out[str(k)] = str(v)
    return out


def _domain_ref(domain: dict[str, Any]) -> OmRef:
    return OmRef(id=str(domain["id"]), type="domain", name=str(domain["name"]))


def _build_patch_ops(
    *,
    table: dict[str, Any],
    desired_tag_fqns: list[str],
    desired_custom_properties: dict[str, str],
    desired_domain_ref: OmRef | None,
) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []

    # Tags (union)
    existing_fqns = _existing_tag_fqns(table)
    merged_fqns = merge_tag_fqns(existing_fqns, desired_tag_fqns)
    if merged_fqns != existing_fqns:
        ops.append({"op": "add" if not table.get("tags") else "replace", "path": "/tags", "value": _tag_labels(merged_fqns)})

    # Custom properties (merge, override desired keys)
    existing_cp = _existing_custom_properties(table)
    merged_cp = dict(existing_cp)
    merged_cp.update(desired_custom_properties)

    ext = table.get("extension")
    if not isinstance(ext, dict) or not ext:
        value: dict[str, Any] = {"customProperties": merged_cp}
        if desired_domain_ref:
            value["domain"] = {
                "id": desired_domain_ref.id,
                "type": desired_domain_ref.type,
                "name": desired_domain_ref.name,
            }
        ops.append({"op": "add", "path": "/extension", "value": value})
    else:
        if merged_cp != existing_cp:
            if "customProperties" not in ext:
                ops.append({"op": "add", "path": "/extension/customProperties", "value": merged_cp})
            else:
                ops.append({"op": "replace", "path": "/extension/customProperties", "value": merged_cp})

    # Domain (best-effort; depends on OM version/entity shape)
    if desired_domain_ref:
        desired_domain_value = {"id": desired_domain_ref.id, "type": desired_domain_ref.type, "name": desired_domain_ref.name}
        current_domain = None
        current_domain_id = None
        if isinstance(ext, dict):
            current_domain = ext.get("domain")
        if isinstance(current_domain, dict):
            current_domain_id = current_domain.get("id")
        if current_domain_id != desired_domain_ref.id and current_domain != desired_domain_value:
            if not isinstance(ext, dict) or not ext:
                # extension already handled above; domain will be included on next run
                pass
            else:
                op = "add" if "domain" not in ext else "replace"
                ops.append({"op": op, "path": "/extension/domain", "value": desired_domain_value})

    return ops


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TFM: enrich OpenMetadata assets with DCAT-like governance metadata")
    repo_root = Path(__file__).resolve().parents[3]
    default_defaults = repo_root / "tfm_ingestor" / "config" / "governance_defaults.yaml"
    default_rules = repo_root / "tfm_ingestor" / "config" / "mapping_rules.yaml"

    parser.add_argument("--defaults", default=str(default_defaults), help="Defaults YAML path")
    parser.add_argument("--rules", default=str(default_rules), help="Rules YAML path")
    parser.add_argument("--base-url", default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"), help="OpenMetadata base URL (api/v1)")
    parser.add_argument("--token", default=os.getenv("OPENMETADATA_JWT_TOKEN"), help="OpenMetadata JWT token")
    parser.add_argument("--limit", type=int, default=1000, help="Max tables to read from OM (PoC)")
    parser.add_argument("--dry-run", action="store_true", help="Print plan, do not PATCH anything")
    args = parser.parse_args(argv)

    defaults = load_defaults(args.defaults)
    rules = load_rules(args.rules)

    api = OpenMetadataApi(base_url=args.base_url, jwt_token=args.token)

    fields = "tags,extension,schema"
    try:
        tables = api.list_tables(limit=args.limit, fields=fields)
    except OpenMetadataApiError as e:
        raise SystemExit(f"ERROR: cannot list tables from OpenMetadata: {e}") from e

    planned: list[dict[str, Any]] = []
    applied = 0
    domain_cache: dict[str, OmRef] = {}

    for t in tables:
        schema_ref = t.get("schema") or t.get("databaseSchema") or {}
        schema_name = (schema_ref or {}).get("name") if isinstance(schema_ref, dict) else None
        table_name = t.get("name")
        fqn = t.get("fullyQualifiedName")
        table_id = t.get("id")
        if not (schema_name and table_name and fqn and table_id):
            continue

        schema_name = str(schema_name)
        table_name = str(table_name)

        if schema_name not in rules.schema_to_layer:
            continue

        spec = build_governance_spec(
            schema_name=schema_name,
            table_name=table_name,
            schema_to_layer=rules.schema_to_layer,
            schema_to_domain=rules.schema_to_domain,
            tags_by_prefix=rules.table_tags_by_prefix,
            catalog_defaults={
                "publisher_name": defaults.catalog.publisher_name,
                "contact_email": defaults.catalog.contact_email,
                "spatial": defaults.catalog.spatial,
                "language": defaults.catalog.language,
                "license_default": defaults.catalog.license_default,
            },
            dataset_defaults={k: str(v) for k, v in defaults.dataset_defaults.items()},
        )

        domain_ref: OmRef | None = None
        if spec.domain_name:
            domain_ref = domain_cache.get(spec.domain_name)
            if domain_ref is None:
                dom = api.get_domain_by_name(domain_name=spec.domain_name)
                if dom is None:
                    dom = api.create_domain(name=spec.domain_name, description="TFM demo domain")
                domain_ref = _domain_ref(dom)
                domain_cache[spec.domain_name] = domain_ref

        ops = _build_patch_ops(
            table=t,
            desired_tag_fqns=spec.tag_fqns,
            desired_custom_properties=spec.custom_properties,
            desired_domain_ref=domain_ref,
        )
        if not ops:
            continue

        planned.append({"tableFQN": str(fqn), "ops": ops})

        if args.dry_run:
            continue

        try:
            api.patch_table(table_id=str(table_id), patch_ops=ops)
            applied += 1
        except OpenMetadataApiError as e:
            raise SystemExit(f"ERROR: patch failed for {fqn}: {e}") from e

    print(json.dumps({"dry_run": bool(args.dry_run), "planned": planned, "applied": applied}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
