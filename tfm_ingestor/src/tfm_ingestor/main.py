from __future__ import annotations

import argparse
import json
import os
import sys

from tfm_ingestor.config import load_ckan_harvest, load_defaults, load_rules
from tfm_ingestor.dcat_export import export_catalog
from tfm_ingestor.governance_service import discover_tables, load_tables_input, run_governance_sync
from tfm_ingestor.governance_sheet import generate_governance_sheet, load_governance_sheet
from tfm_ingestor.harvest_ckan import run_harvest
from tfm_ingestor.om_api import OpenMetadataApi, OpenMetadataApiError
from tfm_ingestor.operational_profile import load_operational_profile
from tfm_ingestor.runtime import repo_paths
from tfm_ingestor.runtime_validation import validate_runtime_state, write_runtime_validation_report
from tfm_ingestor.shacl_validation import export_and_validate_catalog, validate_jsonld_file
from tfm_ingestor.workflow_service import WorkflowRunConfig, run_workflow


def cli_enrich(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="TFM: enrich OpenMetadata assets with DCAT-AP-ES governance metadata (active HVD profile)"
    )
    paths = repo_paths()

    parser.add_argument("--defaults", default=str(paths.defaults_path), help="Defaults YAML path")
    parser.add_argument("--rules", default=str(paths.rules_path), help="Rules YAML path")
    parser.add_argument("--sheet", default=str(paths.sheet_path), help="Governance sheet CSV path (Excel-friendly)")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"),
        help="OpenMetadata base URL (api/v1)",
    )
    parser.add_argument("--token", default=os.getenv("OPENMETADATA_JWT_TOKEN"), help="OpenMetadata JWT token")
    parser.add_argument("--limit", type=int, default=1000, help="Max tables to read from OM (PoC)")
    parser.add_argument("--tables-in", default=None, help="Read OpenMetadata tables from a JSON file (offline mode)")
    parser.add_argument("--plan-output", default=None, help="Write reproducible JSON plan to a file")
    parser.add_argument("--dry-run", action="store_true", help="Print plan, do not PATCH anything")
    args = parser.parse_args(argv)

    defaults = load_defaults(args.defaults)
    rules = load_rules(args.rules)
    tables_input = load_tables_input(args.tables_in) if args.tables_in else None
    api = None if tables_input is not None else OpenMetadataApi(base_url=args.base_url, jwt_token=args.token)
    sheet_rows = load_governance_sheet(args.sheet) if args.sheet and os.path.exists(args.sheet) else []

    try:
        result = run_governance_sync(
            defaults=defaults,
            rules=rules,
            api=api,
            limit=int(args.limit),
            dry_run=bool(args.dry_run),
            sheet_rows=sheet_rows,
            tables_input=tables_input,
            plan_output=args.plan_output,
        )
    except (OpenMetadataApiError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cli_generate_governance_sheet(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="TFM: generate governance sheet CSV for non-technical metadata curation"
    )
    paths = repo_paths()

    parser.add_argument("--defaults", default=str(paths.defaults_path), help="Defaults YAML path")
    parser.add_argument("--rules", default=str(paths.rules_path), help="Rules YAML path")
    parser.add_argument("--output", default=str(paths.sheet_path), help="Output governance CSV path")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"),
        help="OpenMetadata base URL (api/v1)",
    )
    parser.add_argument("--token", default=os.getenv("OPENMETADATA_JWT_TOKEN"), help="OpenMetadata JWT token")
    parser.add_argument("--limit", type=int, default=1000, help="Max tables to read from OM")
    parser.add_argument("--tables-in", default=None, help="Read OpenMetadata tables from a JSON file (offline mode)")
    args = parser.parse_args(argv)

    defaults = load_defaults(args.defaults)
    rules = load_rules(args.rules)
    tables_input = load_tables_input(args.tables_in) if args.tables_in else None
    api = None if tables_input is not None else OpenMetadataApi(base_url=args.base_url, jwt_token=args.token)
    tables = discover_tables(api=api, limit=int(args.limit), tables_input=tables_input)

    existing_rows: list[object] = []
    if os.path.exists(args.output):
        try:
            existing_rows = load_governance_sheet(args.output)
        except ValueError:
            existing_rows = []

    written = generate_governance_sheet(
        tables=tables,
        defaults=defaults,
        output_path=args.output,
        existing_rows=existing_rows,
        tags_by_prefix=rules.table_tags_by_prefix,
    )
    print(json.dumps({"output_path": str(args.output), "rows_written": written}, indent=2, ensure_ascii=False))
    return 0


def cli_validate_governance_sheet(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TFM: validate governance sheet CSV")
    paths = repo_paths()

    parser.add_argument("--sheet", default=str(paths.sheet_path), help="Governance sheet CSV path")
    args = parser.parse_args(argv)

    try:
        rows = load_governance_sheet(args.sheet)
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "conforms": False,
                    "row_count": 0,
                    "errors": [str(exc)],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 2

    print(
        json.dumps(
            {
                "conforms": True,
                "row_count": len(rows),
                "errors": [],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cli_harvest_ckan(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TFM: harvest CKAN metadata and enrich OpenMetadata tables")
    paths = repo_paths()

    parser.add_argument("--config", default=str(paths.harvest_config_path), help="CKAN harvest YAML config")
    parser.add_argument("--defaults", default=str(paths.defaults_path), help="Defaults YAML path (catalog)")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"),
        help="OpenMetadata base URL (api/v1)",
    )
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
        with open(args.datasets_in, "r", encoding="utf-8-sig") as file_obj:
            datasets_input = json.load(file_obj)
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
    parser = argparse.ArgumentParser(
        description="TFM: export OpenMetadata catalog to DCAT-AP-ES JSON-LD (active HVD profile)"
    )
    paths = repo_paths()

    parser.add_argument("--defaults", default=str(paths.defaults_path), help="Defaults YAML path (catalog)")
    parser.add_argument("--rules", default=str(paths.rules_path), help="Rules YAML path (used to filter schemas)")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"),
        help="OpenMetadata base URL (api/v1)",
    )
    parser.add_argument("--token", default=os.getenv("OPENMETADATA_JWT_TOKEN"), help="OpenMetadata JWT token")
    parser.add_argument("--limit", type=int, default=1000, help="Max tables to read from OM")
    parser.add_argument("--tables-in", default=None, help="Read OpenMetadata tables from a JSON file (offline mode)")
    parser.add_argument("--output", default="dcat_catalog.jsonld", help="Output JSON-LD path")
    args = parser.parse_args(argv)

    defaults = load_defaults(args.defaults)
    rules = load_rules(args.rules)
    tables_input = load_tables_input(args.tables_in) if args.tables_in else None
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


def cli_validate_dcat(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TFM: validate DCAT-AP-ES JSON-LD against bundled SHACL shapes")
    paths = repo_paths()

    parser.add_argument("--input", default=None, help="Existing JSON-LD file to validate")
    parser.add_argument("--defaults", default=str(paths.defaults_path), help="Defaults YAML path (catalog)")
    parser.add_argument("--rules", default=str(paths.rules_path), help="Rules YAML path (used to filter schemas)")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"),
        help="OpenMetadata base URL (api/v1)",
    )
    parser.add_argument("--token", default=os.getenv("OPENMETADATA_JWT_TOKEN"), help="OpenMetadata JWT token")
    parser.add_argument("--limit", type=int, default=1000, help="Max tables to read from OM")
    parser.add_argument("--tables-in", default=None, help="Read OpenMetadata tables from a JSON file (offline mode)")
    parser.add_argument("--export-output", default="dcat_catalog.jsonld", help="JSON-LD output path when exporting before validating")
    parser.add_argument("--shapes", default=None, help="Override bundled SHACL shapes path")
    parser.add_argument("--profile-case", choices=["base", "hvd"], default="hvd", help="Bundled SHACL profile to validate against")
    parser.add_argument("--report-output", default=None, help="Write SHACL validation report as Turtle")
    parser.add_argument("--allow-warnings", action="store_true", help="Treat SHACL warnings as non-blocking")
    args = parser.parse_args(argv)

    try:
        if args.input:
            result = validate_jsonld_file(
                input_path=args.input,
                shapes_path=args.shapes,
                profile_case=str(args.profile_case),
                allow_warnings=bool(args.allow_warnings),
                report_output=args.report_output,
            )
        else:
            defaults = load_defaults(args.defaults)
            rules = load_rules(args.rules)
            tables_input = load_tables_input(args.tables_in) if args.tables_in else None
            api = None if tables_input is not None else OpenMetadataApi(base_url=args.base_url, jwt_token=args.token)
            result = export_and_validate_catalog(
                defaults=defaults,
                rules=rules,
                om_api=api,
                limit_tables=int(args.limit),
                tables_input=tables_input,
                export_output=args.export_output,
                shapes_path=args.shapes,
                profile_case=str(args.profile_case),
                allow_warnings=bool(args.allow_warnings),
                report_output=args.report_output,
            )
    except (OpenMetadataApiError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cli_validate_runtime(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="TFM: validate live OpenMetadata state against SQL demo contract and governed metadata"
    )
    paths = repo_paths()

    parser.add_argument("--rules", default=str(paths.rules_path), help="Rules YAML path")
    parser.add_argument("--sheet", default=str(paths.sheet_path), help="Governance sheet CSV path")
    parser.add_argument("--sql", default=str(paths.sql_demo_path), help="SQL demo contract path")
    parser.add_argument("--service-name", default="postgres_demo_service", help="Expected OpenMetadata database service name")
    parser.add_argument("--database-name", default="opendata_demo", help="Expected OpenMetadata database name")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"),
        help="OpenMetadata base URL (api/v1)",
    )
    parser.add_argument("--token", default=os.getenv("OPENMETADATA_JWT_TOKEN"), help="OpenMetadata JWT token")
    parser.add_argument("--limit", type=int, default=1000, help="Max tables to read from OM")
    parser.add_argument("--tables-in", default=None, help="Read OpenMetadata tables from a JSON file (offline mode)")
    parser.add_argument("--output", default=None, help="Write runtime validation report as JSON")
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero code when validation does not conform")
    args = parser.parse_args(argv)

    try:
        tables_input = load_tables_input(args.tables_in) if args.tables_in else None
        api = None if tables_input is not None else OpenMetadataApi(base_url=args.base_url, jwt_token=args.token)
        result = validate_runtime_state(
            sql_path=args.sql,
            sheet_path=args.sheet,
            rules_path=args.rules,
            service_name=args.service_name,
            database_name=args.database_name,
            api=api,
            limit=int(args.limit),
            tables_input=tables_input,
        )
    except (OpenMetadataApiError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    if args.output:
        write_runtime_validation_report(args.output, result)
        result["output"] = str(args.output)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if bool(args.strict) and not bool(result.get("conforms")):
        raise SystemExit(2)
    return 0


def cli_workflow_run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="TFM: canonical workflow for discover, plan, apply, export and validate"
    )
    paths = repo_paths()

    parser.add_argument("--profile", default=str(paths.operational_profile_path), help="Operational profile YAML path")
    parser.add_argument("--defaults", default=None, help="Override defaults YAML path")
    parser.add_argument("--rules", default=None, help="Override rules YAML path")
    parser.add_argument("--sheet", default=None, help="Override governance sheet CSV path")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENMETADATA_BASE_URL", "http://localhost:8585/api/v1"),
        help="OpenMetadata base URL (api/v1)",
    )
    parser.add_argument("--token", default=os.getenv("OPENMETADATA_JWT_TOKEN"), help="OpenMetadata JWT token")
    parser.add_argument("--limit", type=int, default=1000, help="Max tables to read from OM")
    parser.add_argument("--tables-in", default=None, help="Read OpenMetadata tables from a JSON file (offline mode)")
    parser.add_argument("--export-output", default=None, help="Override JSON-LD output path")
    parser.add_argument("--report-output", default=None, help="Override SHACL validation report path")
    parser.add_argument("--profile-case", choices=["base", "hvd"], default=None, help="Override bundled SHACL profile")
    parser.add_argument("--plan-output", default=None, help="Write reproducible workflow plan to a file")
    parser.add_argument("--allow-warnings", action="store_true", help="Treat SHACL warnings as non-blocking")
    parser.add_argument("--dry-run", action="store_true", help="Refresh sheet and generate plan without applying")
    parser.add_argument("--skip-sheet-refresh", action="store_true", help="Do not refresh governance sheet before planning")
    parser.add_argument("--skip-export", action="store_true", help="Skip export step after apply")
    parser.add_argument("--skip-validate", action="store_true", help="Skip SHACL validation step after apply")
    args = parser.parse_args(argv)

    try:
        profile = load_operational_profile(
            args.profile,
            repo_root=paths.repo_root,
            defaults_path=paths.defaults_path,
            rules_path=paths.rules_path,
            sheet_path=paths.sheet_path,
            harvest_config_path=paths.harvest_config_path,
        )
        result = run_workflow(
            WorkflowRunConfig(
                defaults_path=args.defaults or str(profile.defaults_path),
                rules_path=args.rules or str(profile.rules_path),
                sheet_path=args.sheet or str(profile.sheet_path),
                base_url=args.base_url,
                token=args.token,
                limit=int(args.limit),
                dry_run=bool(args.dry_run),
                refresh_sheet=bool(profile.workflow.refresh_sheet) and not bool(args.skip_sheet_refresh),
                export_output=args.export_output or profile.workflow.export_output,
                report_output=args.report_output if args.report_output is not None else profile.workflow.report_output,
                allow_warnings=bool(args.allow_warnings) or bool(profile.workflow.allow_warnings),
                profile_case=str(args.profile_case or profile.workflow.profile_case),
                plan_output=args.plan_output,
                tables_input_path=args.tables_in,
                skip_export=bool(args.skip_export),
                skip_validate=bool(args.skip_validate),
            )
        )
    except (OpenMetadataApiError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cli(argv: list[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] == "generate-governance-sheet":
        return cli_generate_governance_sheet(args[1:])
    if args and args[0] == "validate-governance-sheet":
        return cli_validate_governance_sheet(args[1:])
    if args and args[0] == "harvest-ckan":
        return cli_harvest_ckan(args[1:])
    if args and args[0] == "export-dcat":
        return cli_export_dcat(args[1:])
    if args and args[0] == "validate-dcat":
        return cli_validate_dcat(args[1:])
    if args and args[0] == "validate-runtime":
        return cli_validate_runtime(args[1:])
    if args and args[0] == "workflow":
        if len(args) > 1 and args[1] == "run":
            return cli_workflow_run(args[2:])
        return cli_workflow_run(args[1:])
    return cli_enrich(args)


if __name__ == "__main__":
    raise SystemExit(cli())
