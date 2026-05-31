from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tfm_ingestor.config import RulesConfig, load_rules
from tfm_ingestor.governance_service import MANAGED_DCAT_CUSTOM_PROPERTIES
from tfm_ingestor.governance_sheet import GovernanceSheetRow, load_governance_sheet
from tfm_ingestor.om_api import OpenMetadataApi, OpenMetadataApiError
from tfm_ingestor.patch_ops import existing_custom_properties, existing_tag_fqns


ACTIVE_GOVERNANCE_CUSTOM_PROPERTIES = [
    "dcat_publisher_name",
    "dcat_hvd_category",
    "dcat_access_url",
]


def _list_tables_for_validation(*, api: OpenMetadataApi, limit: int) -> list[dict[str, Any]]:
    field_candidates = [
        "columns,tags,extension,domains,databaseSchema,schema",
        "columns,tags,extension,domains,databaseSchema",
        "columns,tags,extension,databaseSchema",
        "columns,tags,extension",
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


def _schema_name(table: dict[str, Any]) -> str:
    schema_ref = table.get("schema") or table.get("databaseSchema") or {}
    if isinstance(schema_ref, dict) and schema_ref.get("name"):
        return str(schema_ref["name"]).strip()
    fqn = str(table.get("fullyQualifiedName") or "").strip()
    parts = fqn.split(".")
    if len(parts) >= 4:
        return parts[-2]
    return ""


def _table_key(*, schema_name: str, table_name: str) -> str:
    return f"{schema_name}.{table_name}"


def _table_contract_key(*, service_name: str, database_name: str, schema_name: str, table_name: str) -> str:
    return f"{service_name}.{database_name}.{schema_name}.{table_name}"


def _split_service_names(raw: str) -> list[str]:
    names = [part.strip() for part in re.split(r"[,;]", raw) if part.strip()]
    return names or [raw.strip()]


def _parse_table_fqn(fqn: str) -> tuple[str | None, str | None, str | None, str | None]:
    parts = [part.strip() for part in fqn.split(".") if part.strip()]
    if len(parts) < 4:
        return None, None, None, None
    return parts[-4], parts[-3], parts[-2], parts[-1]


def _parse_sql_contract(sql_text: str) -> dict[str, Any]:
    schema_matches = re.findall(r"CREATE\s+SCHEMA\s+IF\s+NOT\s+EXISTS\s+([a-zA-Z_][\w]*)\s*;", sql_text, flags=re.IGNORECASE)
    table_matches = re.finditer(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\s*\((.*?)\)\s*;",
        sql_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    tables: list[dict[str, Any]] = []
    for match in table_matches:
        schema_name = str(match.group(1))
        table_name = str(match.group(2))
        body = str(match.group(3))
        columns: list[str] = []
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line:
                continue
            upper = line.upper()
            if upper.startswith(("PRIMARY KEY", "FOREIGN KEY", "CONSTRAINT", "UNIQUE", "CHECK")):
                continue
            column_name = line.split()[0].strip('"')
            columns.append(column_name)
        tables.append(
            {
                "schema_name": schema_name,
                "table_name": table_name,
                "columns": columns,
            }
        )

    return {
        "schemas": sorted(dict.fromkeys(schema_matches)),
        "tables": tables,
    }


def load_sql_contract(path: str | Path) -> dict[str, Any]:
    sql_path = Path(path)
    return _parse_sql_contract(sql_path.read_text(encoding="utf-8"))


def _domains_for_table(table: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for item in table.get("domains") or []:
        if isinstance(item, dict) and item.get("name"):
            out.append(str(item["name"]).strip())
    return out


def _columns_for_table(table: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for item in table.get("columns") or []:
        if isinstance(item, dict) and item.get("name"):
            out.append(str(item["name"]).strip())
    return out


def validate_runtime_state(
    *,
    sql_path: str | Path,
    sheet_path: str | Path,
    rules_path: str | Path,
    service_name: str,
    database_name: str,
    api: OpenMetadataApi | None = None,
    limit: int = 1000,
    tables_input: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    contract = load_sql_contract(sql_path)
    rules = load_rules(rules_path)
    sheet_rows = load_governance_sheet(sheet_path)
    tables = [item for item in tables_input if isinstance(item, dict)] if tables_input is not None else _list_tables_for_validation(api=api, limit=limit)  # type: ignore[arg-type]
    expected_service_names = _split_service_names(service_name)

    service_names_from_api: list[str] = []
    database_names_from_api: list[str] = []
    schema_names_from_api: list[str] = []
    if api is not None:
        try:
            service_names_from_api = sorted(
                str(item.get("name")).strip()
                for item in api.list_database_services(limit=100)
                if isinstance(item, dict) and item.get("name")
            )
        except OpenMetadataApiError:
            service_names_from_api = []
        try:
            database_names_from_api = sorted(
                str(item.get("name")).strip()
                for item in api.list_databases(limit=100)
                if isinstance(item, dict) and item.get("name")
            )
        except OpenMetadataApiError:
            database_names_from_api = []
        try:
            schema_names_from_api = sorted(
                str(item.get("name")).strip()
                for item in api.list_database_schemas(limit=100)
                if isinstance(item, dict) and item.get("name")
            )
        except OpenMetadataApiError:
            schema_names_from_api = []

    actual_tables_by_key: dict[str, dict[str, Any]] = {}
    actual_tables_by_fqn: dict[str, dict[str, Any]] = {}
    detected_service_names: set[str] = set()
    detected_database_names: set[str] = set()
    detected_schema_names: set[str] = set()
    for table in tables:
        table_name = str(table.get("name") or "").strip()
        schema_name = _schema_name(table)
        if not schema_name or not table_name:
            continue
        fqn = str(table.get("fullyQualifiedName") or "").strip()
        if fqn:
            actual_tables_by_fqn[fqn] = table
        detected_schema_names.add(schema_name)
        service, database, parsed_schema, parsed_table = _parse_table_fqn(fqn)
        if service:
            detected_service_names.add(service)
        if database:
            detected_database_names.add(database)
        if service in expected_service_names and database == database_name:
            key = _table_contract_key(
                service_name=service,
                database_name=database,
                schema_name=parsed_schema or schema_name,
                table_name=parsed_table or table_name,
            )
            actual_tables_by_key[key] = table

    expected_tables = contract["tables"]
    expected_keys = {
        _table_contract_key(
            service_name=expected_service,
            database_name=database_name,
            schema_name=item["schema_name"],
            table_name=item["table_name"],
        )
        for expected_service in expected_service_names
        for item in expected_tables
    }
    actual_keys = set(actual_tables_by_key.keys())

    missing_tables = sorted(expected_keys - actual_keys)
    unexpected_tables = sorted(actual_keys - expected_keys)

    column_checks: list[dict[str, Any]] = []
    technical_issues: list[str] = []
    for expected_service in expected_service_names:
        for expected in expected_tables:
            key = _table_contract_key(
                service_name=expected_service,
                database_name=database_name,
                schema_name=expected["schema_name"],
                table_name=expected["table_name"],
            )
            actual_table = actual_tables_by_key.get(key)
            if actual_table is None:
                column_checks.append(
                    {
                        "table": key,
                        "conforms": False,
                        "reason": "missing_table",
                        "expected_columns": expected["columns"],
                        "actual_columns": [],
                    }
                )
                continue
            actual_columns = _columns_for_table(actual_table)
            conforms = actual_columns == expected["columns"]
            if not conforms:
                technical_issues.append(f"Column mismatch in {key}")
            column_checks.append(
                {
                    "table": key,
                    "conforms": conforms,
                    "expected_columns": expected["columns"],
                    "actual_columns": actual_columns,
                }
            )

    expected_schemas = sorted(contract["schemas"])
    actual_schema_source = schema_names_from_api or sorted(detected_schema_names)
    missing_schemas = sorted(set(expected_schemas) - set(actual_schema_source))

    detected_service_source = service_names_from_api or sorted(detected_service_names)
    missing_services = sorted(set(expected_service_names) - set(detected_service_source))
    service_present = not missing_services
    database_present = database_name in (database_names_from_api or sorted(detected_database_names))
    if missing_services:
        technical_issues.append(f"Missing database services: {', '.join(missing_services)}")
    if not database_present:
        technical_issues.append(f"Missing database: {database_name}")
    if missing_schemas:
        technical_issues.append(f"Missing schemas: {', '.join(missing_schemas)}")
    if missing_tables:
        technical_issues.append(f"Missing tables: {', '.join(missing_tables)}")
    if unexpected_tables:
        technical_issues.append(f"Unexpected tables: {', '.join(unexpected_tables)}")

    published_rows = [row for row in sheet_rows if row.publish]
    governance_checks: list[dict[str, Any]] = []
    governance_issues: list[str] = []
    legacy_managed_keys = [key for key in MANAGED_DCAT_CUSTOM_PROPERTIES if key not in ACTIVE_GOVERNANCE_CUSTOM_PROPERTIES]
    for row in published_rows:
        key = row.table_fqn or _table_key(schema_name=row.schema_name, table_name=row.table_name)
        table = actual_tables_by_fqn.get(row.table_fqn) if row.table_fqn else None
        issues: list[str] = []
        if table is None and row.table_fqn:
            for candidate in tables:
                if str(candidate.get("fullyQualifiedName") or "").strip() == row.table_fqn:
                    table = candidate
                    break
        if table is None and len(expected_service_names) == 1:
            fallback_key = _table_contract_key(
                service_name=expected_service_names[0],
                database_name=database_name,
                schema_name=row.schema_name,
                table_name=row.table_name,
            )
            table = actual_tables_by_key.get(fallback_key)
        if table is None:
            issues.append("missing_live_table")
            governance_issues.append(f"Missing live table for governance row: {key}")
            governance_checks.append({"table": key, "conforms": False, "issues": issues})
            continue

        actual_display_name = str(table.get("displayName") or table.get("name") or "").strip()
        actual_description = str(table.get("description") or "").strip()
        actual_tags = sorted([tag for tag in existing_tag_fqns(table) if tag.startswith("dcat_theme.")])
        actual_cp = existing_custom_properties(table)
        actual_domains = _domains_for_table(table)

        if actual_display_name != row.title:
            issues.append("displayName_mismatch")
        if actual_description != row.description:
            issues.append("description_mismatch")
        if actual_tags != sorted(row.theme_tag_fqns):
            issues.append("theme_tags_mismatch")

        expected_cp = {
            "dcat_publisher_name": row.publisher_name,
            "dcat_hvd_category": row.hvd_category_uri,
            "dcat_access_url": row.distribution_access_url,
        }
        for cp_key, cp_value in expected_cp.items():
            if str(actual_cp.get(cp_key) or "").strip() != cp_value:
                issues.append(f"{cp_key}_mismatch")

        legacy_present = sorted(key for key in legacy_managed_keys if key in actual_cp)
        if legacy_present:
            issues.append("legacy_custom_properties_present")

        expected_domain = rules.schema_to_domain.get(row.schema_name)
        if expected_domain:
            if actual_domains != [expected_domain]:
                issues.append("domain_mismatch")

        if issues:
            governance_issues.append(f"Governance mismatch in {key}: {', '.join(issues)}")
        governance_checks.append(
            {
                "table": key,
                "conforms": not issues,
                "issues": issues,
                "actual_display_name": actual_display_name,
                "actual_description": actual_description,
                "actual_theme_tags": actual_tags,
                "actual_custom_properties": {key: actual_cp.get(key, "") for key in ACTIVE_GOVERNANCE_CUSTOM_PROPERTIES},
                "actual_domains": actual_domains,
                "legacy_custom_properties_present": legacy_present,
            }
        )

    technical_summary = {
        "conforms": not technical_issues,
        "service_name_expected": service_name,
        "service_names_expected": expected_service_names,
        "service_name_present": service_present,
        "service_names_detected": sorted(detected_service_source),
        "missing_services": missing_services,
        "database_name_expected": database_name,
        "database_name_present": database_present,
        "database_names_detected": sorted(database_names_from_api or detected_database_names),
        "schemas_expected": expected_schemas,
        "schemas_detected": actual_schema_source,
        "missing_schemas": missing_schemas,
        "tables_expected_count": len(expected_tables),
        "tables_detected_count": len(actual_tables_by_key),
        "missing_tables": missing_tables,
        "unexpected_tables": unexpected_tables,
        "column_checks": column_checks,
        "issues": technical_issues,
    }
    governance_summary = {
        "conforms": not governance_issues,
        "published_datasets_expected": len(published_rows),
        "checks": governance_checks,
        "issues": governance_issues,
    }
    return {
        "technical": technical_summary,
        "governance": governance_summary,
        "conforms": technical_summary["conforms"] and governance_summary["conforms"],
    }


def write_runtime_validation_report(path: str | Path, report: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
