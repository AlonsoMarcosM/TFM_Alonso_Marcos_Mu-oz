from tfm_ingestor.config import CatalogDefaults, CkanConfig, CkanHarvestConfig, DefaultsConfig
from tfm_ingestor.harvest_ckan import build_plan


def test_build_plan_creates_patch_ops_for_mapped_dataset():
    defaults = DefaultsConfig(
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
            },
        },
        hvd_defaults={},
    )

    cfg = CkanHarvestConfig(
        ckan=CkanConfig(
            base_url="https://demo.ckan.org",
            fallback_base_urls=[],
            query="",
            rows=10,
            start=0,
            resource_index=0,
            max_datasets=None,
        ),
        dataset_to_table_fqn={"bici-uso": "svc.db.bronze.bici_uso_raw"},
        theme_to_tag_fqn={"transport": "dcat_theme.transporte"},
        write_description=True,
        write_display_name=True,
    )

    table = {
        "id": "t1",
        "fullyQualifiedName": "svc.db.bronze.bici_uso_raw",
        "name": "bici_uso_raw",
        "displayName": "Bici uso (old)",
        "description": "",
        "tags": [],
        "extension": {
            "dct_license": "legacy-license",
            "dcat_hvd_category": "http://data.europa.eu/bna/c_e1da4e07",
            "dcat_access_url": "https://legacy.example.org",
        },
    }
    om_tables_by_fqn = {table["fullyQualifiedName"]: table}

    dataset = {
        "id": "ckan-1",
        "name": "bici-uso",
        "title": "Bici uso",
        "notes": "Dataset de uso de bicicletas",
        "license_id": "cc-by",
        "maintainer_email": "contacto@opendata.es",
        "organization": {"title": "Ayuntamiento"},
        "tags": [{"name": "bici"}],
        "groups": [{"name": "transport"}],
        "resources": [{"url": "https://demo.ckan.org/dataset/bici-uso.csv"}],
    }

    planned, skipped = build_plan(
        ckan_cfg=cfg,
        defaults=defaults,
        om_tables_by_fqn=om_tables_by_fqn,
        datasets=[dataset],
    )
    assert skipped == []
    assert len(planned) == 1

    ops = planned[0].ops
    paths = [op["path"] for op in ops]
    assert "/description" in paths
    assert "/displayName" in paths
    assert "/tags" in paths
    assert "/extension" in paths

    merged_cp = None
    for op in ops:
        if op["path"] == "/extension" and isinstance(op.get("value"), dict):
            merged_cp = op["value"]
    assert isinstance(merged_cp, dict)
    assert merged_cp["dcat_publisher_name"] == "Ayuntamiento"
    assert merged_cp["dcat_hvd_category"] == "http://data.europa.eu/bna/c_b79e35eb"
    assert merged_cp["dcat_access_url"] == "https://demo.ckan.org/dataset/bici-uso.csv"
    assert "dct_license" not in merged_cp
