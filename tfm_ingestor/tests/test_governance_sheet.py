from pathlib import Path

from tfm_ingestor.config import CatalogDefaults, DefaultsConfig
from tfm_ingestor.governance_sheet import generate_governance_sheet, load_governance_sheet, match_sheet_row


def _defaults() -> DefaultsConfig:
    return DefaultsConfig(
        catalog=CatalogDefaults(
            title="Demo",
            description="Demo",
            publisher_name="UCLM",
            publisher_uri="http://datos.gob.es/recurso/sector-publico/org/Organismo/U03400001",
            homepage="https://example.org",
            theme_taxonomy="http://datos.gob.es/kos/sector-publico/sector",
            issued="2026-02-05",
            modified="2026-02-05",
            language="http://publications.europa.eu/resource/authority/language/SPA",
            license_default="https://example.org/legal",
        ),
        dataset_defaults={
            "access_url_base": "https://example.org/datos/poc",
            "hvd_category_by_theme_tag": {
                "dcat_theme.transporte": "movilidad",
                "dcat_theme.cultura_ocio": "estadisticas",
            },
        },
        hvd_defaults={},
    )


def test_load_governance_sheet_parses_excel_friendly_csv(tmp_path: Path):
    path = tmp_path / "sheet.csv"
    path.write_text(
        "\n".join(
            [
                "publicar;schema_name;table_name;table_fqn;titulo_dataset;descripcion_dataset;publicador;tematica_dcat;categoria_hvd;access_url_distribucion",
                "si;gold;movilidad_resumen_municipio;svc.db.gold.movilidad_resumen_municipio;Movilidad;Descripcion;UCLM;transporte;movilidad;https://example.org/datos/poc/gold/movilidad",
                "no;gold;agenda_cultural_publica;svc.db.gold.agenda_cultural_publica;;;;cultura_ocio;;",
            ]
        ),
        encoding="utf-8-sig",
    )

    rows = load_governance_sheet(path)
    assert len(rows) == 2
    assert rows[0].publish is True
    assert rows[0].theme_tag_fqns == ["dcat_theme.transporte"]
    assert rows[0].hvd_category_uri == "http://data.europa.eu/bna/c_b79e35eb"
    assert rows[0].distribution_access_url == "https://example.org/datos/poc/gold/movilidad"
    assert rows[1].publish is False


def test_load_governance_sheet_accepts_official_controlled_vocabularies(tmp_path: Path):
    path = tmp_path / "sheet.csv"
    path.write_text(
        "\n".join(
            [
                "publicar;schema_name;table_name;table_fqn;titulo_dataset;descripcion_dataset;publicador;tematica_dcat;categoria_hvd;access_url_distribucion",
                "si;gold;observacion;svc.db.gold.observacion;Observacion;Descripcion;UCLM;medio_ambiente;observacion_de_la_tierra_y_medio_ambiente;https://example.org/datos/poc/gold/observacion",
            ]
        ),
        encoding="utf-8-sig",
    )

    rows = load_governance_sheet(path)

    assert rows[0].theme_tag_fqns == ["dcat_theme.medio_ambiente"]
    assert rows[0].hvd_category_uri == "http://data.europa.eu/bna/c_dd313021"


def test_generate_governance_sheet_writes_only_gold_tables(tmp_path: Path):
    defaults = _defaults()
    output = tmp_path / "sheet.csv"
    tables = [
        {
            "fullyQualifiedName": "svc.db.gold.movilidad_resumen_municipio",
            "name": "movilidad_resumen_municipio",
            "displayName": "Movilidad",
            "description": "Resumen de movilidad",
            "tags": [{"tagFQN": "dcat_theme.transporte"}],
            "extension": {
                "dcat_publisher_name": "UCLM",
                "dcat_access_url": "https://example.org/datos/poc/gold/movilidad-resumen-municipio",
            },
            "databaseSchema": {"name": "gold"},
        },
        {
            "fullyQualifiedName": "svc.db.silver.bici_uso_diario",
            "name": "bici_uso_diario",
            "databaseSchema": {"name": "silver"},
        },
    ]

    written = generate_governance_sheet(tables=tables, defaults=defaults, output_path=output)
    assert written == 1
    content = output.read_text(encoding="utf-8-sig")
    assert "movilidad_resumen_municipio" in content
    assert "movilidad" in content
    assert "https://example.org/datos/poc/gold/movilidad-resumen-municipio" in content
    assert "bici_uso_diario" not in content


def test_match_sheet_row_resolves_by_schema_and_table():
    rows = load_governance_sheet(Path(__file__).resolve().parents[1] / "config" / "gold_governance.csv")
    table = {
        "fullyQualifiedName": "svc.db.gold.movilidad_resumen_municipio",
        "name": "movilidad_resumen_municipio",
        "databaseSchema": {"name": "gold"},
    }
    row = match_sheet_row(rows=rows, table=table)
    assert row is not None
    assert row.table_name == "movilidad_resumen_municipio"


def test_generate_governance_sheet_preserves_existing_manual_curation(tmp_path: Path):
    defaults = _defaults()
    output = tmp_path / "sheet.csv"
    output.write_text(
        "\n".join(
            [
                "publicar;schema_name;table_name;table_fqn;titulo_dataset;descripcion_dataset;publicador;tematica_dcat;categoria_hvd;access_url_distribucion",
                "no;gold;movilidad_resumen_municipio;svc.db.gold.movilidad_resumen_municipio;Título funcional;Descripción funcional;;transporte;movilidad;https://example.org/curada",
            ]
        ),
        encoding="utf-8-sig",
    )

    tables = [
        {
            "fullyQualifiedName": "svc.db.gold.movilidad_resumen_municipio",
            "name": "movilidad_resumen_municipio",
            "displayName": "Título técnico",
            "description": "Descripción técnica",
            "tags": [{"tagFQN": "dcat_theme.cultura_ocio"}],
            "extension": {
                "dcat_publisher_name": "OpenMetadata",
                "dcat_hvd_category": "http://data.europa.eu/bna/c_e1da4e07",
                "dcat_access_url": "https://example.org/tecnica",
            },
            "databaseSchema": {"name": "gold"},
        }
    ]

    written = generate_governance_sheet(
        tables=tables,
        defaults=defaults,
        output_path=output,
        existing_rows=load_governance_sheet(output),
    )

    assert written == 1
    content = output.read_text(encoding="utf-8-sig")
    assert (
        "no;gold;movilidad_resumen_municipio;svc.db.gold.movilidad_resumen_municipio;"
        "Título funcional;Descripción funcional;;transporte;movilidad;https://example.org/curada"
    ) in content
