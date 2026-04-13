from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tfm_ingestor.config import DefaultsConfig, RulesConfig
from tfm_ingestor.governance_model import GovernanceIntent, PlannedTableChange
from tfm_ingestor.governance_sheet import GovernanceSheetRow, match_sheet_row
from tfm_ingestor.mapping import build_governance_spec
from tfm_ingestor.om_api import OpenMetadataApi, OpenMetadataApiError, OmRef
from tfm_ingestor.patch_ops import build_table_patch_ops


MANAGED_DCAT_CUSTOM_PROPERTIES = [
    "dcat_publisher_name",
    "dcat_hvd_category",
    "dcat_contact_email",
    "dct_spatial",
    "dct_language",
    "dct_license",
    "dct_issued",
    "dct_modified",
    "dct_temporal",
    "dct_accrual_periodicity",
    "dcat_access_url",
    "dcat_download_url",
    "dcat_endpoint_url",
    "dcat_landing_page",
    "dct_identifier",
    "tfm_layer",
]
MANAGED_DCAT_TAG_PREFIXES = ["dcat_theme.", "dcat_keyword."]


def load_tables_input(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8-sig") as file_obj:
        data = json.load(file_obj)
    if not isinstance(data, list):
        raise ValueError("--tables-in must be a JSON array of OpenMetadata tables")
    return [item for item in data if isinstance(item, dict)]


def list_tables_with_fallback(*, api: OpenMetadataApi, limit: int) -> list[dict[str, Any]]:
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
            tables = api.list_tables(limit=limit, fields=fields)
            break
        except OpenMetadataApiError as exc:
            last_error = exc
            if "Invalid field name" in str(exc):
                continue
            raise
    if tables is None:
        raise OpenMetadataApiError(f"cannot list tables from OpenMetadata: {last_error}")
    return tables


def schema_name_for_table(table: dict[str, Any]) -> str | None:
    schema_ref = table.get("schema") or table.get("databaseSchema") or {}
    if isinstance(schema_ref, dict) and schema_ref.get("name"):
        return str(schema_ref["name"])
    return None


def discover_tables(
    *,
    api: OpenMetadataApi | None,
    limit: int,
    tables_input: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if tables_input is not None:
        return [item for item in tables_input if isinstance(item, dict)]
    if api is None:
        raise ValueError("discover_tables requires api or tables_input")
    return list_tables_with_fallback(api=api, limit=limit)


def build_governance_intents(
    *,
    tables: list[dict[str, Any]],
    defaults: DefaultsConfig,
    rules: RulesConfig,
    sheet_rows: list[GovernanceSheetRow] | None = None,
) -> list[GovernanceIntent]:
    intents: list[GovernanceIntent] = []
    rows = sheet_rows or []
    use_sheet = bool(rows)

    for table in tables:
        schema_name = schema_name_for_table(table)
        table_name = str(table.get("name") or "").strip()
        table_fqn = str(table.get("fullyQualifiedName") or "").strip()
        if not (schema_name and table_name and table_fqn):
            continue
        if schema_name not in rules.schema_to_layer:
            continue

        row = match_sheet_row(rows=rows, table=table) if use_sheet else None
        if use_sheet and row is None:
            continue

        if row is not None:
            intents.append(
                GovernanceIntent(
                    table_fqn=table_fqn,
                    schema_name=schema_name,
                    table_name=table_name,
                    publish=row.publish,
                    title=row.title if row.publish else None,
                    description=row.description if row.publish else None,
                    publisher_name=(row.publisher_name or defaults.catalog.publisher_name) if row.publish else None,
                    theme_tag_fqns=row.theme_tag_fqns if row.publish else [],
                    hvd_category_uri=row.hvd_category_uri if row.publish else None,
                    distribution_access_url=row.distribution_access_url if row.publish else None,
                    source="sheet",
                )
            )
            continue

        spec = build_governance_spec(
            schema_name=schema_name,
            table_name=table_name,
            schema_to_layer=rules.schema_to_layer,
            schema_to_domain=rules.schema_to_domain,
            tags_by_prefix=rules.table_tags_by_prefix,
            catalog_defaults={"publisher_name": defaults.catalog.publisher_name},
            dataset_defaults=defaults.dataset_defaults,
        )
        intents.append(
            GovernanceIntent(
                table_fqn=table_fqn,
                schema_name=schema_name,
                table_name=table_name,
                publish=True,
                title=None,
                description=None,
                publisher_name=str(spec.custom_properties.get("dcat_publisher_name") or defaults.catalog.publisher_name),
                theme_tag_fqns=spec.tag_fqns,
                hvd_category_uri=str(spec.custom_properties.get("dcat_hvd_category") or "") or None,
                distribution_access_url=str(spec.custom_properties.get("dcat_access_url") or "") or None,
                source="rules",
                domain_name=spec.domain_name,
            )
        )

    return intents


def _domain_ref(domain: dict[str, Any]) -> OmRef:
    return OmRef(id=str(domain["id"]), type="domain", name=str(domain["name"]))


def _resolve_domain_ref(
    *,
    api: OpenMetadataApi | None,
    dry_run: bool,
    domain_name: str | None,
    domain_cache: dict[str, OmRef],
) -> OmRef | None:
    if not domain_name or api is None:
        return None
    ref = domain_cache.get(domain_name)
    if ref is not None:
        return ref
    domain = api.get_domain_by_name(domain_name=domain_name)
    if domain is None and not dry_run:
        domain = api.create_domain(
            name=domain_name,
            description="TFM demo domain",
            domain_type="Source-aligned",
        )
    if domain is None:
        return None
    ref = _domain_ref(domain)
    domain_cache[domain_name] = ref
    return ref


def plan_governance_changes(
    *,
    tables: list[dict[str, Any]],
    intents: list[GovernanceIntent],
    api: OpenMetadataApi | None = None,
    dry_run: bool = True,
) -> list[PlannedTableChange]:
    intent_by_fqn = {intent.table_fqn: intent for intent in intents}
    domain_cache: dict[str, OmRef] = {}
    planned: list[PlannedTableChange] = []

    for table in tables:
        table_fqn = str(table.get("fullyQualifiedName") or "").strip()
        table_id = str(table.get("id") or "").strip()
        if not table_fqn or not table_id:
            continue
        intent = intent_by_fqn.get(table_fqn)
        if intent is None:
            continue

        desired_tag_fqns = intent.theme_tag_fqns if intent.publish else []
        desired_custom_properties = (
            {
                "dcat_publisher_name": intent.publisher_name or "",
                "dcat_hvd_category": intent.hvd_category_uri or "",
                "dcat_access_url": intent.distribution_access_url or "",
            }
            if intent.publish
            else {}
        )
        desired_custom_properties = {k: v for k, v in desired_custom_properties.items() if v}

        domain_ref = _resolve_domain_ref(
            api=api,
            dry_run=dry_run,
            domain_name=intent.domain_name,
            domain_cache=domain_cache,
        )
        ops = build_table_patch_ops(
            table=table,
            desired_tag_fqns=desired_tag_fqns,
            desired_custom_properties=desired_custom_properties,
            desired_domain_ref=domain_ref,
            desired_description=intent.description if intent.publish else None,
            desired_display_name=intent.title if intent.publish else None,
            managed_tag_prefixes=MANAGED_DCAT_TAG_PREFIXES,
            managed_custom_property_keys=MANAGED_DCAT_CUSTOM_PROPERTIES,
        )
        if not ops:
            continue
        planned.append(
            PlannedTableChange(
                table_fqn=table_fqn,
                table_id=table_id,
                ops=ops,
            )
        )
    return planned


def apply_governance_changes(*, api: OpenMetadataApi, planned_changes: list[PlannedTableChange]) -> int:
    applied = 0
    for change in planned_changes:
        api.patch_table(table_id=change.table_id, patch_ops=change.ops)
        applied += 1
    return applied


def run_governance_sync(
    *,
    defaults: DefaultsConfig,
    rules: RulesConfig,
    api: OpenMetadataApi | None = None,
    limit: int = 1000,
    dry_run: bool = False,
    sheet_rows: list[GovernanceSheetRow] | None = None,
    tables_input: list[dict[str, Any]] | None = None,
    plan_output: str | Path | None = None,
) -> dict[str, Any]:
    tables = discover_tables(api=api, limit=limit, tables_input=tables_input)
    intents = build_governance_intents(
        tables=tables,
        defaults=defaults,
        rules=rules,
        sheet_rows=sheet_rows,
    )
    planned_changes = plan_governance_changes(
        tables=tables,
        intents=intents,
        api=api,
        dry_run=dry_run,
    )
    applied = 0
    if not dry_run:
        if api is None:
            raise ValueError("run_governance_sync requires api when dry_run is false")
        applied = apply_governance_changes(api=api, planned_changes=planned_changes)

    summary = {
        "dry_run": bool(dry_run),
        "intents": len(intents),
        "planned": [change.as_dict() for change in planned_changes],
        "applied": applied,
    }
    if plan_output is not None:
        Path(plan_output).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        summary["plan_output"] = str(plan_output)
    return summary
