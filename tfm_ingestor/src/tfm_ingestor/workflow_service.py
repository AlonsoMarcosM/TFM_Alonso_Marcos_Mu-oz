from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tfm_ingestor.config import load_defaults, load_rules
from tfm_ingestor.dcat_export import export_catalog
from tfm_ingestor.governance_service import discover_tables, load_tables_input, run_governance_sync
from tfm_ingestor.governance_sheet import generate_governance_sheet, load_governance_sheet
from tfm_ingestor.om_api import OpenMetadataApi
from tfm_ingestor.shacl_validation import export_and_validate_catalog


@dataclass(frozen=True)
class WorkflowRunConfig:
    defaults_path: str
    rules_path: str
    sheet_path: str
    base_url: str
    token: str | None
    limit: int = 1000
    dry_run: bool = False
    refresh_sheet: bool = True
    export_output: str = "dcat_catalog.jsonld"
    report_output: str | None = None
    allow_warnings: bool = False
    profile_case: str = "hvd"
    plan_output: str | None = None
    tables_input_path: str | None = None
    skip_export: bool = False
    skip_validate: bool = False


def run_workflow(config: WorkflowRunConfig) -> dict[str, Any]:
    defaults = load_defaults(config.defaults_path)
    rules = load_rules(config.rules_path)
    tables_input = load_tables_input(config.tables_input_path) if config.tables_input_path else None
    api = None if tables_input is not None else OpenMetadataApi(base_url=config.base_url, jwt_token=config.token)
    tables = discover_tables(api=api, limit=config.limit, tables_input=tables_input)

    sheet_rows: list[Any] = []
    sheet_refreshed = False
    if config.refresh_sheet:
        existing_rows: list[Any] = []
        if Path(config.sheet_path).exists():
            try:
                existing_rows = load_governance_sheet(config.sheet_path)
            except ValueError:
                existing_rows = []
        generate_governance_sheet(
            tables=tables,
            defaults=defaults,
            output_path=config.sheet_path,
            existing_rows=existing_rows,
            tags_by_prefix=rules.table_tags_by_prefix,
        )
        sheet_refreshed = True
    sheet_validation_error: str | None = None
    if Path(config.sheet_path).exists():
        try:
            sheet_rows = load_governance_sheet(config.sheet_path)
        except ValueError as exc:
            if not config.dry_run:
                raise
            sheet_validation_error = str(exc)

    sync_summary: dict[str, Any] | None = None
    if sheet_validation_error is None:
        sync_summary = run_governance_sync(
            defaults=defaults,
            rules=rules,
            api=api,
            limit=config.limit,
            dry_run=config.dry_run,
            sheet_rows=sheet_rows,
            tables_input=tables_input,
            plan_output=config.plan_output,
        )

    export_summary: dict[str, Any] | None = None
    validation_summary: dict[str, Any] | None = None
    if not config.dry_run and sheet_validation_error is None:
        if not config.skip_validate:
            validation_summary = export_and_validate_catalog(
                defaults=defaults,
                rules=rules,
                om_api=api,
                limit_tables=config.limit,
                tables_input=tables_input,
                export_output=config.export_output,
                profile_case=config.profile_case,
                allow_warnings=config.allow_warnings,
                report_output=config.report_output,
            )
        elif not config.skip_export:
            export_summary = export_catalog(
                defaults=defaults,
                rules=rules,
                om_api=api,
                limit_tables=config.limit,
                tables_input=tables_input,
                output_path=config.export_output,
            )

    return {
        "workflow": {
            "dry_run": bool(config.dry_run),
            "sheet_refreshed": sheet_refreshed,
            "sheet_path": config.sheet_path,
            "profile_case": config.profile_case,
            "tables_discovered": len(tables),
            "sheet_rows_loaded": len(sheet_rows),
            "sheet_valid": sheet_validation_error is None,
            "sheet_validation_error": sheet_validation_error,
        },
        "sync": sync_summary,
        "export": export_summary,
        "validation": validation_summary,
    }
