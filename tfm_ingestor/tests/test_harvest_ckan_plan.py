from tfm_ingestor.config import CatalogDefaults, CkanConfig, CkanHarvestConfig, DefaultsConfig
from tfm_ingestor.harvest_ckan import build_plan


def test_build_plan_creates_patch_ops_for_mapped_dataset():
    defaults = DefaultsConfig(
        catalog=CatalogDefaults(
            title="Demo",
            description="Demo",
            publisher_name="UCLM",
            contact_email="demo@uclm.es",
            homepage="https://example.org",
            theme_taxonomy="https://example.org/themes",
            issued="2026-02-05",
            modified="2026-02-05",
            spatial="ES-CLM",
            language="es",
            license_default="CC-BY-4.0",
        ),
        dataset_defaults={"accrual_periodicity": "daily"},
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
        keyword_to_tag_fqn={"bici": "dcat_keyword.bici"},
        theme_to_tag_fqn={"transport": "dcat_theme.transport"},
        extras_to_custom_properties={},
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
        "extension": {"customProperties": {}},
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
        "extras": [{"key": "language", "value": "es"}],
        "metadata_created": "2026-02-01T10:00:00Z",
        "metadata_modified": "2026-02-04T12:00:00Z",
        "resources": [{"url": "https://example.org/data.csv"}],
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
    assert "/extension/customProperties" in paths or "/extension" in paths

    merged_cp = None
    for op in ops:
        if op["path"] == "/extension/customProperties":
            merged_cp = op["value"]
        if op["path"] == "/extension" and isinstance(op.get("value"), dict):
            merged_cp = op["value"].get("customProperties")
    assert isinstance(merged_cp, dict)
    assert merged_cp["dct_identifier"] == "ckan-1"
    assert merged_cp["dcat_landing_page"].endswith("/dataset/bici-uso")
    assert merged_cp["dcat_access_url"] == "https://example.org/data.csv"
    assert merged_cp["dcat_download_url"] == "https://example.org/data.csv"
    assert merged_cp["dct_issued"] == "2026-02-01T10:00:00Z"
    assert merged_cp["dct_modified"] == "2026-02-04T12:00:00Z"
