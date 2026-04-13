import json
from pathlib import Path

from tfm_ingestor.workflow_service import WorkflowRunConfig, run_workflow


def _write_defaults(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "catalog:",
                '  title: "Open Data Demo"',
                '  description: "Catálogo demo"',
                '  publisher_name: "UCLM"',
                '  publisher_uri: "http://datos.gob.es/recurso/sector-publico/org/Organismo/U03400001"',
                '  homepage: "https://example.org"',
                '  theme_taxonomy: "http://datos.gob.es/kos/sector-publico/sector"',
                '  issued: "2026-02-05"',
                '  modified: "2026-02-05"',
                '  language: "http://publications.europa.eu/resource/authority/language/SPA"',
                '  license_default: "https://example.org/legal"',
                "dataset_defaults:",
                '  access_url_base: "https://example.org/datos/poc"',
                "  hvd_category_by_theme_tag:",
                '    dcat_theme.transporte: "movilidad"',
                "hvd_defaults:",
                "  enabled: true",
                '  applicable_legislation: "http://data.europa.eu/eli/reg_impl/2023/138/oj"',
                '  distribution_license: "http://publications.europa.eu/resource/authority/licence/CC_BY_4_0"',
                '  access_rights: "http://publications.europa.eu/resource/authority/access-right/PUBLIC"',
                '  service_endpoint_url_base: "https://example.org/api"',
                '  service_endpoint_description_base: "https://example.org/api-docs"',
                '  service_documentation_base: "https://example.org/docs"',
                "  contact:",
                '    organization_name: "UCLM"',
                '    fn: "Oficina demo de datos abiertos"',
                '    has_uid: "http://datos.gob.es/recurso/sector-publico/org/Organismo/U03400001"',
                '    has_email: "mailto:opendata-demo@example.org"',
                '    has_url: "https://example.org/contacto"',
                '    has_telephone: "tel:+34902000000"',
            ]
        ),
        encoding="utf-8",
    )


def _write_rules(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "schema_to_layer:",
                '  gold: "Gold"',
                "schema_to_domain: {}",
                "table_tags_by_prefix:",
                '  movilidad_: ["dcat_theme.transporte"]',
            ]
        ),
        encoding="utf-8",
    )


def test_run_workflow_dry_run_refreshes_sheet_and_writes_plan(tmp_path: Path):
    defaults_path = tmp_path / "defaults.yaml"
    rules_path = tmp_path / "rules.yaml"
    sheet_path = tmp_path / "gold_governance.csv"
    tables_path = tmp_path / "tables.json"
    plan_output = tmp_path / "plan.json"
    _write_defaults(defaults_path)
    _write_rules(rules_path)

    tables_path.write_text(
        json.dumps(
            [
                {
                    "id": "table-1",
                    "fullyQualifiedName": "svc.db.gold.movilidad_resumen_municipio",
                    "name": "movilidad_resumen_municipio",
                    "description": "Resumen de movilidad por municipio",
                    "tags": [],
                    "extension": {},
                    "databaseSchema": {"name": "gold"},
                }
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = run_workflow(
        WorkflowRunConfig(
            defaults_path=str(defaults_path),
            rules_path=str(rules_path),
            sheet_path=str(sheet_path),
            base_url="http://localhost:8585/api/v1",
            token=None,
            dry_run=True,
            refresh_sheet=True,
            plan_output=str(plan_output),
            tables_input_path=str(tables_path),
        )
    )

    assert sheet_path.exists()
    assert plan_output.exists()
    assert result["workflow"]["sheet_refreshed"] is True
    assert result["workflow"]["sheet_valid"] is True
    assert result["workflow"]["tables_discovered"] == 1
    assert result["sync"] is not None
    assert result["sync"]["dry_run"] is True
    assert len(result["sync"]["planned"]) == 1
    assert result["export"] is None
    assert result["validation"] is None


def test_run_workflow_dry_run_reports_sheet_curation_needed(tmp_path: Path):
    defaults_path = tmp_path / "defaults.yaml"
    rules_path = tmp_path / "rules.yaml"
    sheet_path = tmp_path / "gold_governance.csv"
    tables_path = tmp_path / "tables.json"
    _write_defaults(defaults_path)
    _write_rules(rules_path)

    tables_path.write_text(
        json.dumps(
            [
                {
                    "id": "table-1",
                    "fullyQualifiedName": "svc.db.gold.otra_tabla",
                    "name": "otra_tabla",
                    "description": "",
                    "tags": [],
                    "extension": {},
                    "databaseSchema": {"name": "gold"},
                }
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = run_workflow(
        WorkflowRunConfig(
            defaults_path=str(defaults_path),
            rules_path=str(rules_path),
            sheet_path=str(sheet_path),
            base_url="http://localhost:8585/api/v1",
            token=None,
            dry_run=True,
            refresh_sheet=True,
            tables_input_path=str(tables_path),
        )
    )

    assert result["workflow"]["sheet_refreshed"] is True
    assert result["workflow"]["sheet_valid"] is False
    assert "descripcion_dataset" in str(result["workflow"]["sheet_validation_error"])
    assert result["sync"] is None
    assert result["export"] is None
    assert result["validation"] is None


def test_run_workflow_apply_and_export_uses_canonical_service_layer(monkeypatch, tmp_path: Path):
    defaults_path = tmp_path / "defaults.yaml"
    rules_path = tmp_path / "rules.yaml"
    sheet_path = tmp_path / "gold_governance.csv"
    export_output = tmp_path / "catalog.jsonld"
    _write_defaults(defaults_path)
    _write_rules(rules_path)
    sheet_path.write_text(
        "\n".join(
            [
                "publicar;schema_name;table_name;table_fqn;titulo_dataset;descripcion_dataset;publicador;tematica_dcat;categoria_hvd;access_url_distribucion",
                "si;gold;movilidad_resumen_municipio;svc.db.gold.movilidad_resumen_municipio;Movilidad municipal;Resumen de movilidad por municipio;UCLM;transporte;movilidad;https://example.org/datos/poc/gold/movilidad-resumen-municipio",
            ]
        ),
        encoding="utf-8-sig",
    )

    class DummyApi:
        tables = [
            {
                "id": "table-1",
                "fullyQualifiedName": "svc.db.gold.movilidad_resumen_municipio",
                "name": "movilidad_resumen_municipio",
                "description": "Resumen técnico",
                "tags": [],
                "extension": {},
                "databaseSchema": {"name": "gold"},
            }
        ]
        patches: list[tuple[str, list[dict[str, object]]]] = []

        def __init__(self, *, base_url: str, jwt_token: str | None) -> None:
            self.base_url = base_url
            self.jwt_token = jwt_token

        def list_tables(self, *, limit: int = 1000, fields: str | None = None):
            return [json.loads(json.dumps(item)) for item in self.tables[:limit]]

        def patch_table(self, *, table_id: str, patch_ops: list[dict[str, object]]) -> None:
            self.patches.append((table_id, patch_ops))
            for table in self.tables:
                if table.get("id") != table_id:
                    continue
                for op in patch_ops:
                    path = str(op["path"])
                    if path == "/displayName":
                        table["displayName"] = op["value"]
                    elif path == "/description":
                        table["description"] = op["value"]
                    elif path == "/tags":
                        table["tags"] = op["value"]
                    elif path == "/extension":
                        table["extension"] = op["value"]
                    elif path == "/domains":
                        table["domains"] = op["value"]

    monkeypatch.setattr("tfm_ingestor.workflow_service.OpenMetadataApi", DummyApi)

    result = run_workflow(
        WorkflowRunConfig(
            defaults_path=str(defaults_path),
            rules_path=str(rules_path),
            sheet_path=str(sheet_path),
            base_url="http://localhost:8585/api/v1",
            token="token-demo",
            dry_run=False,
            refresh_sheet=False,
            export_output=str(export_output),
            skip_validate=True,
        )
    )

    assert result["sync"] is not None
    assert result["sync"]["applied"] == 1
    assert result["export"] is not None
    assert result["export"]["tables_exported"] == 1
    assert result["export"]["preview_dataset_count"] == 1
    assert result["validation"] is None
    assert export_output.exists()
    assert DummyApi.patches
