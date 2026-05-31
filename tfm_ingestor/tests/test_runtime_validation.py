import json
from pathlib import Path

from tfm_ingestor.runtime_validation import load_sql_contract, validate_runtime_state


def _write_rules(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "schema_to_layer:",
                '  gold: "Gold"',
                "schema_to_domain: {}",
                "table_tags_by_prefix:",
                '  movilidad_: ["dcat_theme.transporte"]',
                '  agenda_: ["dcat_theme.cultura_ocio"]',
            ]
        ),
        encoding="utf-8",
    )


def _write_sheet(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "publicar;schema_name;table_name;table_fqn;titulo_dataset;descripcion_dataset;publicador;tematica_dcat;categoria_hvd;access_url_distribucion",
                "si;gold;movilidad_resumen_municipio;postgres_demo_service.opendata_demo.gold.movilidad_resumen_municipio;Resumen movilidad;Resumen de movilidad municipal;UCLM;transporte;movilidad;https://example.org/datos/plataforma-gobierno-dato/gold/movilidad-resumen-municipio",
                "si;gold;agenda_cultural_publica;postgres_demo_service.opendata_demo.gold.agenda_cultural_publica;Agenda cultural;Agenda pública cultural;UCLM;cultura_ocio;estadisticas;https://example.org/datos/plataforma-gobierno-dato/gold/agenda-cultural-publica",
            ]
        ),
        encoding="utf-8-sig",
    )


def _write_sql(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "CREATE SCHEMA IF NOT EXISTS bronze;",
                "CREATE SCHEMA IF NOT EXISTS silver;",
                "CREATE SCHEMA IF NOT EXISTS gold;",
                "CREATE TABLE IF NOT EXISTS bronze.bici_uso_raw (",
                "  event_id BIGSERIAL PRIMARY KEY,",
                "  ts TIMESTAMP NOT NULL,",
                "  estacion_id INT NOT NULL,",
                "  viajes INT NOT NULL,",
                "  fuente TEXT NOT NULL",
                ");",
                "CREATE TABLE IF NOT EXISTS bronze.eventos_raw (",
                "  evento_id BIGSERIAL PRIMARY KEY,",
                "  titulo TEXT NOT NULL,",
                "  fecha DATE NOT NULL,",
                "  municipio TEXT NOT NULL,",
                "  categoria TEXT NOT NULL,",
                "  asistentes_est INT",
                ");",
                "CREATE TABLE IF NOT EXISTS silver.bici_uso_diario (",
                "  fecha DATE NOT NULL,",
                "  estacion_id INT NOT NULL,",
                "  viajes_totales INT NOT NULL,",
                "  PRIMARY KEY (fecha, estacion_id)",
                ");",
                "CREATE TABLE IF NOT EXISTS silver.eventos_normalizados (",
                "  evento_id BIGINT PRIMARY KEY,",
                "  titulo TEXT NOT NULL,",
                "  fecha DATE NOT NULL,",
                "  municipio TEXT NOT NULL,",
                "  categoria_std TEXT NOT NULL,",
                "  asistentes_est INT",
                ");",
                "CREATE TABLE IF NOT EXISTS gold.movilidad_resumen_municipio (",
                "  fecha DATE NOT NULL,",
                "  municipio TEXT NOT NULL,",
                "  viajes_totales INT NOT NULL,",
                "  PRIMARY KEY (fecha, municipio)",
                ");",
                "CREATE TABLE IF NOT EXISTS gold.agenda_cultural_publica (",
                "  evento_id BIGINT PRIMARY KEY,",
                "  titulo TEXT NOT NULL,",
                "  fecha DATE NOT NULL,",
                "  municipio TEXT NOT NULL,",
                "  categoria TEXT NOT NULL,",
                "  asistentes_est INT",
                ");",
            ]
        ),
        encoding="utf-8",
    )


def test_load_sql_contract_extracts_schemas_tables_and_columns(tmp_path: Path):
    sql_path = tmp_path / "referencia.sql"
    _write_sql(sql_path)

    contract = load_sql_contract(sql_path)

    assert contract["schemas"] == ["bronze", "gold", "silver"]
    gold_table = next(item for item in contract["tables"] if item["table_name"] == "movilidad_resumen_municipio")
    assert gold_table["schema_name"] == "gold"
    assert gold_table["columns"] == ["fecha", "municipio", "viajes_totales"]


def test_validate_runtime_state_reports_conforms_for_matching_offline_state(tmp_path: Path):
    sql_path = tmp_path / "referencia.sql"
    rules_path = tmp_path / "rules.yaml"
    sheet_path = tmp_path / "gold_governance.csv"
    _write_sql(sql_path)
    _write_rules(rules_path)
    _write_sheet(sheet_path)

    tables = [
        {
            "id": "1",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.bronze.bici_uso_raw",
            "name": "bici_uso_raw",
            "columns": [{"name": "event_id"}, {"name": "ts"}, {"name": "estacion_id"}, {"name": "viajes"}, {"name": "fuente"}],
            "databaseSchema": {"name": "bronze"},
            "tags": [],
            "extension": {},
        },
        {
            "id": "2",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.bronze.eventos_raw",
            "name": "eventos_raw",
            "columns": [{"name": "evento_id"}, {"name": "titulo"}, {"name": "fecha"}, {"name": "municipio"}, {"name": "categoria"}, {"name": "asistentes_est"}],
            "databaseSchema": {"name": "bronze"},
            "tags": [],
            "extension": {},
        },
        {
            "id": "3",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.silver.bici_uso_diario",
            "name": "bici_uso_diario",
            "columns": [{"name": "fecha"}, {"name": "estacion_id"}, {"name": "viajes_totales"}],
            "databaseSchema": {"name": "silver"},
            "tags": [],
            "extension": {},
        },
        {
            "id": "4",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.silver.eventos_normalizados",
            "name": "eventos_normalizados",
            "columns": [{"name": "evento_id"}, {"name": "titulo"}, {"name": "fecha"}, {"name": "municipio"}, {"name": "categoria_std"}, {"name": "asistentes_est"}],
            "databaseSchema": {"name": "silver"},
            "tags": [],
            "extension": {},
        },
        {
            "id": "5",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.gold.movilidad_resumen_municipio",
            "name": "movilidad_resumen_municipio",
            "displayName": "Resumen movilidad",
            "description": "Resumen de movilidad municipal",
            "columns": [{"name": "fecha"}, {"name": "municipio"}, {"name": "viajes_totales"}],
            "databaseSchema": {"name": "gold"},
            "tags": [{"tagFQN": "dcat_theme.transporte"}],
            "extension": {
                "dcat_publisher_name": "UCLM",
                "dcat_hvd_category": "http://data.europa.eu/bna/c_b79e35eb",
                "dcat_access_url": "https://example.org/datos/plataforma-gobierno-dato/gold/movilidad-resumen-municipio",
            },
        },
        {
            "id": "6",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.gold.agenda_cultural_publica",
            "name": "agenda_cultural_publica",
            "displayName": "Agenda cultural",
            "description": "Agenda pública cultural",
            "columns": [{"name": "evento_id"}, {"name": "titulo"}, {"name": "fecha"}, {"name": "municipio"}, {"name": "categoria"}, {"name": "asistentes_est"}],
            "databaseSchema": {"name": "gold"},
            "tags": [{"tagFQN": "dcat_theme.cultura_ocio"}],
            "extension": {
                "dcat_publisher_name": "UCLM",
                "dcat_hvd_category": "http://data.europa.eu/bna/c_e1da4e07",
                "dcat_access_url": "https://example.org/datos/plataforma-gobierno-dato/gold/agenda-cultural-publica",
            },
        },
    ]

    result = validate_runtime_state(
        sql_path=sql_path,
        sheet_path=sheet_path,
        rules_path=rules_path,
        service_name="postgres_demo_service",
        database_name="opendata_demo",
        tables_input=json.loads(json.dumps(tables)),
    )

    assert result["conforms"] is True
    assert result["technical"]["conforms"] is True
    assert result["governance"]["conforms"] is True
    assert result["governance"]["published_datasets_expected"] == 2


def test_validate_runtime_state_detects_governance_and_column_mismatch(tmp_path: Path):
    sql_path = tmp_path / "referencia.sql"
    rules_path = tmp_path / "rules.yaml"
    sheet_path = tmp_path / "gold_governance.csv"
    _write_sql(sql_path)
    _write_rules(rules_path)
    _write_sheet(sheet_path)

    tables = [
        {
            "id": "1",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.bronze.bici_uso_raw",
            "name": "bici_uso_raw",
            "columns": [{"name": "event_id"}, {"name": "ts"}],
            "databaseSchema": {"name": "bronze"},
            "tags": [],
            "extension": {},
        },
        {
            "id": "2",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.bronze.eventos_raw",
            "name": "eventos_raw",
            "columns": [{"name": "evento_id"}, {"name": "titulo"}, {"name": "fecha"}, {"name": "municipio"}, {"name": "categoria"}, {"name": "asistentes_est"}],
            "databaseSchema": {"name": "bronze"},
            "tags": [],
            "extension": {},
        },
        {
            "id": "3",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.silver.bici_uso_diario",
            "name": "bici_uso_diario",
            "columns": [{"name": "fecha"}, {"name": "estacion_id"}, {"name": "viajes_totales"}],
            "databaseSchema": {"name": "silver"},
            "tags": [],
            "extension": {},
        },
        {
            "id": "4",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.silver.eventos_normalizados",
            "name": "eventos_normalizados",
            "columns": [{"name": "evento_id"}, {"name": "titulo"}, {"name": "fecha"}, {"name": "municipio"}, {"name": "categoria_std"}, {"name": "asistentes_est"}],
            "databaseSchema": {"name": "silver"},
            "tags": [],
            "extension": {},
        },
        {
            "id": "5",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.gold.movilidad_resumen_municipio",
            "name": "movilidad_resumen_municipio",
            "displayName": "Título incorrecto",
            "description": "Resumen de movilidad municipal",
            "columns": [{"name": "fecha"}, {"name": "municipio"}, {"name": "viajes_totales"}],
            "databaseSchema": {"name": "gold"},
            "tags": [{"tagFQN": "dcat_theme.transporte"}],
            "extension": {
                "dcat_publisher_name": "UCLM",
                "dcat_hvd_category": "http://data.europa.eu/bna/c_b79e35eb",
                "dcat_access_url": "https://example.org/datos/plataforma-gobierno-dato/gold/movilidad-resumen-municipio",
            },
        },
        {
            "id": "6",
            "fullyQualifiedName": "postgres_demo_service.opendata_demo.gold.agenda_cultural_publica",
            "name": "agenda_cultural_publica",
            "displayName": "Agenda cultural",
            "description": "Agenda pública cultural",
            "columns": [{"name": "evento_id"}, {"name": "titulo"}, {"name": "fecha"}, {"name": "municipio"}, {"name": "categoria"}, {"name": "asistentes_est"}],
            "databaseSchema": {"name": "gold"},
            "tags": [{"tagFQN": "dcat_theme.cultura_ocio"}],
            "extension": {
                "dcat_publisher_name": "UCLM",
                "dcat_hvd_category": "http://data.europa.eu/bna/c_e1da4e07",
                "dcat_access_url": "https://example.org/datos/plataforma-gobierno-dato/gold/agenda-cultural-publica",
                "dct_identifier": "legacy",
            },
        },
    ]

    result = validate_runtime_state(
        sql_path=sql_path,
        sheet_path=sheet_path,
        rules_path=rules_path,
        service_name="postgres_demo_service",
        database_name="opendata_demo",
        tables_input=json.loads(json.dumps(tables)),
    )

    assert result["conforms"] is False
    assert result["technical"]["conforms"] is False
    assert result["governance"]["conforms"] is False
    assert any("Column mismatch" in issue for issue in result["technical"]["issues"])
    assert any("Governance mismatch" in issue for issue in result["governance"]["issues"])


def test_validate_runtime_state_distinguishes_duplicate_tables_across_services(tmp_path: Path):
    sql_path = tmp_path / "referencia.sql"
    rules_path = tmp_path / "rules.yaml"
    sheet_path = tmp_path / "gold_governance.csv"
    _write_sql(sql_path)
    _write_rules(rules_path)
    sheet_path.write_text(
        "\n".join(
            [
                "publicar;schema_name;table_name;table_fqn;titulo_dataset;descripcion_dataset;publicador;tematica_dcat;categoria_hvd;access_url_distribucion",
                "si;gold;movilidad_resumen_municipio;postgres_demo_service.opendata_demo.gold.movilidad_resumen_municipio;Movilidad demo;Resumen demo;UCLM;transporte;movilidad;https://example.org/demo/gold/movilidad",
                "si;gold;agenda_cultural_publica;postgres_demo_service.opendata_demo.gold.agenda_cultural_publica;Agenda demo;Agenda demo;UCLM;cultura_ocio;estadisticas;https://example.org/demo/gold/agenda",
                "si;gold;movilidad_resumen_municipio;postgres_validation_service.opendata_demo.gold.movilidad_resumen_municipio;Movilidad validacion;Resumen validacion;UCLM;transporte;movilidad;https://example.org/validation/gold/movilidad",
                "si;gold;agenda_cultural_publica;postgres_validation_service.opendata_demo.gold.agenda_cultural_publica;Agenda validacion;Agenda validacion;UCLM;cultura_ocio;estadisticas;https://example.org/validation/gold/agenda",
            ]
        ),
        encoding="utf-8-sig",
    )

    tables = []
    for service_name, title_suffix, url_prefix in [
        ("postgres_demo_service", "demo", "demo"),
        ("postgres_validation_service", "validacion", "validation"),
    ]:
        tables.extend(
            [
                {
                    "id": f"{service_name}-1",
                    "fullyQualifiedName": f"{service_name}.opendata_demo.bronze.bici_uso_raw",
                    "name": "bici_uso_raw",
                    "columns": [{"name": "event_id"}, {"name": "ts"}, {"name": "estacion_id"}, {"name": "viajes"}, {"name": "fuente"}],
                    "databaseSchema": {"name": "bronze"},
                    "tags": [],
                    "extension": {},
                },
                {
                    "id": f"{service_name}-2",
                    "fullyQualifiedName": f"{service_name}.opendata_demo.bronze.eventos_raw",
                    "name": "eventos_raw",
                    "columns": [{"name": "evento_id"}, {"name": "titulo"}, {"name": "fecha"}, {"name": "municipio"}, {"name": "categoria"}, {"name": "asistentes_est"}],
                    "databaseSchema": {"name": "bronze"},
                    "tags": [],
                    "extension": {},
                },
                {
                    "id": f"{service_name}-3",
                    "fullyQualifiedName": f"{service_name}.opendata_demo.silver.bici_uso_diario",
                    "name": "bici_uso_diario",
                    "columns": [{"name": "fecha"}, {"name": "estacion_id"}, {"name": "viajes_totales"}],
                    "databaseSchema": {"name": "silver"},
                    "tags": [],
                    "extension": {},
                },
                {
                    "id": f"{service_name}-4",
                    "fullyQualifiedName": f"{service_name}.opendata_demo.silver.eventos_normalizados",
                    "name": "eventos_normalizados",
                    "columns": [{"name": "evento_id"}, {"name": "titulo"}, {"name": "fecha"}, {"name": "municipio"}, {"name": "categoria_std"}, {"name": "asistentes_est"}],
                    "databaseSchema": {"name": "silver"},
                    "tags": [],
                    "extension": {},
                },
                {
                    "id": f"{service_name}-5",
                    "fullyQualifiedName": f"{service_name}.opendata_demo.gold.movilidad_resumen_municipio",
                    "name": "movilidad_resumen_municipio",
                    "displayName": f"Movilidad {title_suffix}",
                    "description": f"Resumen {title_suffix}",
                    "columns": [{"name": "fecha"}, {"name": "municipio"}, {"name": "viajes_totales"}],
                    "databaseSchema": {"name": "gold"},
                    "tags": [{"tagFQN": "dcat_theme.transporte"}],
                    "extension": {
                        "dcat_publisher_name": "UCLM",
                        "dcat_hvd_category": "http://data.europa.eu/bna/c_b79e35eb",
                        "dcat_access_url": f"https://example.org/{url_prefix}/gold/movilidad",
                    },
                },
                {
                    "id": f"{service_name}-6",
                    "fullyQualifiedName": f"{service_name}.opendata_demo.gold.agenda_cultural_publica",
                    "name": "agenda_cultural_publica",
                    "displayName": f"Agenda {title_suffix}",
                    "description": f"Agenda {title_suffix}",
                    "columns": [{"name": "evento_id"}, {"name": "titulo"}, {"name": "fecha"}, {"name": "municipio"}, {"name": "categoria"}, {"name": "asistentes_est"}],
                    "databaseSchema": {"name": "gold"},
                    "tags": [{"tagFQN": "dcat_theme.cultura_ocio"}],
                    "extension": {
                        "dcat_publisher_name": "UCLM",
                        "dcat_hvd_category": "http://data.europa.eu/bna/c_e1da4e07",
                        "dcat_access_url": f"https://example.org/{url_prefix}/gold/agenda",
                    },
                },
            ]
        )

    result = validate_runtime_state(
        sql_path=sql_path,
        sheet_path=sheet_path,
        rules_path=rules_path,
        service_name="postgres_demo_service,postgres_validation_service",
        database_name="opendata_demo",
        tables_input=json.loads(json.dumps(tables)),
    )

    assert result["conforms"] is True
    assert result["technical"]["tables_expected_count"] == 6
    assert result["technical"]["tables_detected_count"] == 12
    assert result["technical"]["service_names_expected"] == ["postgres_demo_service", "postgres_validation_service"]
    assert result["governance"]["published_datasets_expected"] == 4
