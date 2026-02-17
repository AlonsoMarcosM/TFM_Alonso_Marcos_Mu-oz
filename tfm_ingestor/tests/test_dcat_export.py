from tfm_ingestor.config import CatalogDefaults, DefaultsConfig
from tfm_ingestor.dcat_export import build_catalog_jsonld


def test_build_catalog_jsonld_contains_catalog_and_datasets():
    defaults = DefaultsConfig(
        catalog=CatalogDefaults(
            title="Open Data Demo",
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

    tables = [
        {
            "fullyQualifiedName": "svc.db.bronze.bici_uso_raw",
            "name": "bici_uso_raw",
            "displayName": "Bici uso",
            "description": "Dataset de uso de bicis",
            "tags": [
                {"tagFQN": "dcat_keyword.bici"},
                {"tagFQN": "dcat_theme.transport"},
            ],
            "extension": {
                "customProperties": {
                    "dct_identifier": "ckan-1",
                    "dcat_access_url": "https://example.org/data.csv",
                    "dcat_download_url": "https://example.org/data.csv",
                    "dct_license": "CC-BY-4.0",
                }
            },
        }
    ]

    doc = build_catalog_jsonld(tables=tables, defaults=defaults)
    assert "@context" in doc
    graph = doc.get("@graph")
    assert isinstance(graph, list)
    assert graph and graph[0].get("@type") == "dcat:Catalog"

    datasets = [x for x in graph if isinstance(x, dict) and x.get("@type") == "dcat:Dataset"]
    assert len(datasets) == 1
    ds = datasets[0]
    assert ds["dct:identifier"] == "ckan-1"
    assert "dcat:distribution" in ds
    assert "dct:license" not in ds
    dist = ds["dcat:distribution"][0]
    assert dist["dct:license"] == "CC-BY-4.0"
