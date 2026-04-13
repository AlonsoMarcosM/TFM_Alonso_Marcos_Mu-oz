from tfm_ingestor.config import CatalogDefaults, DefaultsConfig, RulesConfig
from tfm_ingestor.dcat_export import build_catalog_jsonld, export_catalog
from tfm_ingestor.om_api import OpenMetadataApiError


def _defaults() -> DefaultsConfig:
    return DefaultsConfig(
        catalog=CatalogDefaults(
            title="Open Data Demo",
            description="Catálogo demo",
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
        hvd_defaults={
            "enabled": True,
            "applicable_legislation": "http://data.europa.eu/eli/reg_impl/2023/138/oj",
            "distribution_license": "http://publications.europa.eu/resource/authority/licence/CC_BY_4_0",
            "access_rights": "http://publications.europa.eu/resource/authority/access-right/PUBLIC",
            "service_endpoint_url_base": "https://example.org/api",
            "service_endpoint_description_base": "https://example.org/api-docs",
            "service_documentation_base": "https://example.org/docs",
            "contact": {
                "organization_name": "UCLM",
                "fn": "Oficina demo de datos abiertos",
                "has_uid": "http://datos.gob.es/recurso/sector-publico/org/Organismo/U03400001",
                "has_email": "mailto:opendata-demo@example.org",
                "has_url": "https://example.org/contacto",
                "has_telephone": "tel:+34902000000",
            },
        },
    )


def test_build_catalog_jsonld_contains_catalog_datasets_distributions_and_hvd_services():
    defaults = _defaults()

    tables = [
        {
            "fullyQualifiedName": "svc.db.gold.bici_uso_raw",
            "name": "bici_uso_raw",
            "displayName": "Bici uso",
            "description": "Dataset de uso de bicis",
            "tags": [{"tagFQN": "dcat_theme.transporte"}],
            "extension": {
                "dcat_publisher_name": "UCLM",
                "dcat_access_url": "https://example.org/datos/bici-uso",
            },
            "databaseSchema": {"name": "gold"},
        }
    ]

    doc = build_catalog_jsonld(tables=tables, defaults=defaults)
    assert "@context" in doc
    graph = doc.get("@graph")
    assert isinstance(graph, list)
    assert graph and graph[0].get("@type") == "dcat:Catalog"

    catalog = graph[0]
    assert catalog["dct:title"] == {"@value": "Open Data Demo", "@language": "es"}
    assert catalog["dct:language"] == {"@id": "http://publications.europa.eu/resource/authority/language/SPA"}
    assert catalog["dct:license"] == {"@id": "https://example.org/legal"}

    datasets = [x for x in graph if isinstance(x, dict) and x.get("@type") == "dcat:Dataset"]
    distributions = [x for x in graph if isinstance(x, dict) and x.get("@type") == "dcat:Distribution"]
    data_services = [x for x in graph if isinstance(x, dict) and x.get("@type") == "dcat:DataService"]
    assert len(datasets) == 1
    assert len(distributions) == 1
    assert len(data_services) == 1

    dataset = datasets[0]
    assert dataset["@id"] == "urn:openmetadata:table:svc.db.gold.bici_uso_raw"
    assert dataset["dct:title"] == {"@value": "Bici uso", "@language": "es"}
    assert dataset["dct:description"] == {"@value": "Dataset de uso de bicis", "@language": "es"}
    assert dataset["dct:publisher"]["@id"] == "http://datos.gob.es/recurso/sector-publico/org/Organismo/U03400001"
    assert dataset["dcat:theme"] == [{"@id": "http://datos.gob.es/kos/sector-publico/sector/transporte"}]
    assert dataset["dcatap:applicableLegislation"] == [{"@id": "http://data.europa.eu/eli/reg_impl/2023/138/oj"}]
    assert dataset["dcatap:hvdCategory"] == [{"@id": "http://data.europa.eu/bna/c_b79e35eb"}]
    assert dataset["dcat:distribution"] == [{"@id": "urn:openmetadata:table:svc.db.gold.bici_uso_raw:distribution"}]

    distribution = distributions[0]
    assert distribution["@id"] == "urn:openmetadata:table:svc.db.gold.bici_uso_raw:distribution"
    assert distribution["dcat:accessURL"] == [{"@id": "https://example.org/datos/bici-uso"}]
    assert distribution["dcatap:applicableLegislation"] == [{"@id": "http://data.europa.eu/eli/reg_impl/2023/138/oj"}]
    assert distribution["dct:license"] == {"@id": "http://publications.europa.eu/resource/authority/licence/CC_BY_4_0"}
    assert distribution["dcat:accessService"] == [{"@id": "urn:openmetadata:table:svc.db.gold.bici_uso_raw:service"}]

    service = data_services[0]
    assert service["@id"] == "urn:openmetadata:table:svc.db.gold.bici_uso_raw:service"
    assert service["dcat:endpointURL"] == [{"@id": "https://example.org/api/gold/bici-uso-raw"}]
    assert service["dcat:endpointDescription"] == [{"@id": "https://example.org/api-docs/gold/bici-uso-raw"}]
    assert service["foaf:page"] == [{"@id": "https://example.org/docs/gold/bici-uso-raw"}]
    assert service["dcat:servesDataset"] == [{"@id": "urn:openmetadata:table:svc.db.gold.bici_uso_raw"}]
    assert service["dcatap:hvdCategory"] == [{"@id": "http://data.europa.eu/bna/c_b79e35eb"}]


def test_build_catalog_jsonld_skips_dataset_without_mandatory_hvd_metadata():
    defaults = DefaultsConfig(
        catalog=_defaults().catalog,
        dataset_defaults={},
        hvd_defaults=_defaults().hvd_defaults,
    )

    tables = [
        {
            "fullyQualifiedName": "svc.db.gold.sin_access",
            "name": "sin_access",
            "displayName": "Sin acceso",
            "description": "Dataset sin URL de acceso",
            "tags": [{"tagFQN": "dcat_theme.transporte"}],
            "extension": {"dcat_publisher_name": "UCLM", "dcat_hvd_category": "http://data.europa.eu/bna/c_b79e35eb"},
            "databaseSchema": {"name": "gold"},
        },
        {
            "fullyQualifiedName": "svc.db.gold.sin_tema",
            "name": "sin_tema",
            "displayName": "Sin tema",
            "description": "Dataset sin tema",
            "tags": [],
            "extension": {
                "dcat_publisher_name": "UCLM",
                "dcat_hvd_category": "http://data.europa.eu/bna/c_b79e35eb",
                "dcat_access_url": "https://example.org/datos/sin-tema",
            },
            "databaseSchema": {"name": "gold"},
        },
        {
            "fullyQualifiedName": "svc.db.gold.sin_hvd",
            "name": "sin_hvd",
            "displayName": "Sin HVD",
            "description": "Dataset sin categoria HVD",
            "tags": [{"tagFQN": "dcat_theme.transporte"}],
            "extension": {"dcat_publisher_name": "UCLM", "dcat_access_url": "https://example.org/datos/sin-hvd"},
            "databaseSchema": {"name": "gold"},
        },
    ]

    doc = build_catalog_jsonld(tables=tables, defaults=defaults)
    datasets = [x for x in doc["@graph"] if isinstance(x, dict) and x.get("@type") == "dcat:Dataset"]
    assert datasets == []


def test_export_catalog_falls_back_when_schema_field_is_not_supported():
    defaults = _defaults()
    rules = RulesConfig(
        schema_to_layer={"gold": "Gold"},
        schema_to_domain={},
        table_tags_by_prefix={},
    )

    class DummyApi:
        def __init__(self) -> None:
            self.fields_calls: list[str] = []

        def list_tables(self, *, limit: int = 1000, fields: str | None = None):
            self.fields_calls.append(str(fields))
            if fields == "tags,extension,databaseSchema,schema":
                raise OpenMetadataApiError('GET /tables -> 400\n{"code":400,"message":"Invalid field name schema"}')
            return [
                {
                    "fullyQualifiedName": "svc.db.gold.bici_uso_raw",
                    "name": "bici_uso_raw",
                    "displayName": "Bici uso",
                    "description": "Dataset de uso de bicis",
                    "tags": [{"tagFQN": "dcat_theme.transporte"}],
                    "extension": {
                        "dcat_publisher_name": "UCLM",
                        "dcat_hvd_category": "http://data.europa.eu/bna/c_b79e35eb",
                        "dcat_access_url": "https://example.org/datos/bici-uso",
                    },
                    "databaseSchema": {"name": "gold"},
                }
            ]

    api = DummyApi()

    result = export_catalog(
        defaults=defaults,
        rules=rules,
        om_api=api,  # type: ignore[arg-type]
        limit_tables=10,
        output_path=None,
    )

    assert api.fields_calls == ["tags,extension,databaseSchema,schema", "tags,extension,databaseSchema"]
    assert result["tables_total"] == 1
    assert result["tables_exported"] == 1
    assert result["preview_dataset_count"] == 1
