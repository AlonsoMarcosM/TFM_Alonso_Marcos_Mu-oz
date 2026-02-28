from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from tfm_ingestor.config import load_ckan_harvest, load_defaults, load_rules
from tfm_ingestor.dcat_export import export_catalog
from tfm_ingestor.harvest_ckan import run_harvest
from tfm_ingestor.mapping import build_governance_spec
from tfm_ingestor.om_api import OpenMetadataApi, OpenMetadataApiError, OmRef
from tfm_ingestor.patch_ops import build_table_patch_ops


def _domain_ref(domain: dict[str, Any]) -> OmRef:
    return OmRef(id=str(domain["id"]), type="domain", name=str(domain["name"]))


def cli_enrich(argv: list[str] | None = None) -> int:
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

    field_candidates = [
        "tags,extension,domains,databaseSchema",
        "tags,extension,domains,schema",
        "tags,extension,databaseSchema",
        "tags,extension,schema",
        "tags,extension",
    ]
    tables: list[dict[str, Any]] | None = None
    last_error: OpenMetadataApiError | None = None
    for fields in field_candidates:
        try:
            tables = api.list_tables(limit=args.limit, fields=fields)
            break
        except OpenMetadataApiError as e:
            last_error = e
            if "Invalid field name" in str(e):
                continue
            raise SystemExit(f"ERROR: cannot list tables from OpenMetadata: {e}") from e

    if tables is None:
        raise SystemExit(f"ERROR: cannot list tables from OpenMetadata: {last_error}")

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
                    if not args.dry_run:
                        dom = api.create_domain(
                            name=spec.domain_name,
                            description="TFM demo domain",
                            domain_type="Source-aligned",
                        )
                if dom is not None:
                    domain_ref = _domain_ref(dom)
                    domain_cache[spec.domain_name] = domain_ref

        ops = build_table_patch_ops(
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


def cli_harvest_ckan(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TFM: harvest datasets from CKAN and enrich OpenMetadata tables")
    repo_root = Path(__file__).resolve().parents[3]
    default_defaults = repo_root / "tfm_ingestor" / "config" / "governance_defaults.yaml"
    default_cfg = repo_root / "tfm_ingestor" / "config" / "ckan_harvest.yaml"

    parser.add_argument("--config", default=str(default_cfg), help="CKAN harvest YAML config")
    parser.add_argument("--defaults", default=str(default_defaults), help="Defaults YAML path (catalog)")
    parser.add_argument("--base-url", default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"), help="OpenMetadata base URL (api/v1)")
    parser.add_argument("--token", default=os.getenv("OPENMETADATA_JWT_TOKEN"), help="OpenMetadata JWT token")
    parser.add_argument("--limit-tables", type=int, default=1000, help="Max tables to read from OM")
    parser.add_argument("--dry-run", action="store_true", help="Print plan, do not PATCH anything")
    parser.add_argument("--max-datasets", type=int, default=None, help="Limit number of CKAN datasets fetched")
    parser.add_argument("--datasets-in", default=None, help="Read CKAN datasets from a JSON file (offline mode)")
    parser.add_argument("--datasets-out", default=None, help="Write harvested CKAN datasets to a JSON file")
    parser.add_argument("--ckan-api-key", default=os.getenv("CKAN_API_KEY"), help="CKAN API key (optional)")
    args = parser.parse_args(argv)

    defaults = load_defaults(args.defaults)
    ckan_cfg = load_ckan_harvest(args.config)

    datasets_input = None
    if args.datasets_in:
        # Accept UTF-8 with BOM (common on Windows)
        with open(args.datasets_in, "r", encoding="utf-8-sig") as f:
            datasets_input = json.load(f)
        if not isinstance(datasets_input, list):
            raise SystemExit("ERROR: --datasets-in must be a JSON array of CKAN datasets")

    api = OpenMetadataApi(base_url=args.base_url, jwt_token=args.token)

    try:
        result = run_harvest(
            ckan_cfg=ckan_cfg,
            defaults=defaults,
            om_api=api,
            dry_run=bool(args.dry_run),
            limit_tables=int(args.limit_tables),
            datasets_input=datasets_input,
            write_datasets_path=args.datasets_out,
            ckan_api_key=args.ckan_api_key,
            max_datasets=args.max_datasets,
        )
    except (OpenMetadataApiError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cli_export_dcat(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TFM: export OpenMetadata catalog to DCAT-AP JSON-LD (MVP)")
    repo_root = Path(__file__).resolve().parents[3]
    default_defaults = repo_root / "tfm_ingestor" / "config" / "governance_defaults.yaml"
    default_rules = repo_root / "tfm_ingestor" / "config" / "mapping_rules.yaml"

    parser.add_argument("--defaults", default=str(default_defaults), help="Defaults YAML path (catalog)")
    parser.add_argument("--rules", default=str(default_rules), help="Rules YAML path (used to filter schemas)")
    parser.add_argument("--base-url", default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"), help="OpenMetadata base URL (api/v1)")
    parser.add_argument("--token", default=os.getenv("OPENMETADATA_JWT_TOKEN"), help="OpenMetadata JWT token")
    parser.add_argument("--limit", type=int, default=1000, help="Max tables to read from OM")
    parser.add_argument("--tables-in", default=None, help="Read OpenMetadata tables from a JSON file (offline mode)")
    parser.add_argument("--output", default="dcat_catalog.jsonld", help="Output JSON-LD path")
    args = parser.parse_args(argv)

    defaults = load_defaults(args.defaults)
    rules = load_rules(args.rules)

    tables_input = None
    if args.tables_in:
        # Accept UTF-8 with BOM (common on Windows)
        with open(args.tables_in, "r", encoding="utf-8-sig") as f:
            tables_input = json.load(f)
        if not isinstance(tables_input, list):
            raise SystemExit("ERROR: --tables-in must be a JSON array of OpenMetadata tables")

    api = None if tables_input is not None else OpenMetadataApi(base_url=args.base_url, jwt_token=args.token)
    result = export_catalog(
        defaults=defaults,
        rules=rules,
        om_api=api,
        limit_tables=int(args.limit),
        tables_input=tables_input,
        output_path=str(args.output) if args.output else None,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cli(argv: list[str] | None = None) -> int:
    """
    Dispatch CLI.

    Backwards compatible:
    - default behavior is `enrich` (previous CLI)
    - new commands:
      - harvest-ckan
      - export-dcat
    """
    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] == "harvest-ckan":
        return cli_harvest_ckan(args[1:])
    if args and args[0] == "export-dcat":
        return cli_export_dcat(args[1:])
    return cli_enrich(args)


if __name__ == "__main__":
    raise SystemExit(cli())
