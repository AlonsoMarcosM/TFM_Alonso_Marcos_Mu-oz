from tfm_ingestor.mapping import (
    build_distribution_access_url,
    build_governance_spec,
    domain_for_schema,
    hvd_category_alias,
    hvd_category_for_tags,
    merge_tag_fqns,
    normalize_hvd_category,
    layer_for_schema,
    tags_for_table,
)


def test_layer_for_schema():
    mapping = {"bronze": "Bronze"}
    assert layer_for_schema("bronze", mapping) == "Bronze"
    assert layer_for_schema("silver", mapping) is None


def test_domain_for_schema():
    mapping = {"bronze": "OpenData_Bronze"}
    assert domain_for_schema("bronze", mapping) == "OpenData_Bronze"
    assert domain_for_schema("silver", mapping) is None


def test_tags_for_table_prefixes_are_applied_and_deduped():
    rules = {"bici_": ["dcat_theme.transporte"], "bici_uso": ["dcat_theme.transporte"]}
    tags = tags_for_table("bici_uso_raw", rules)
    assert tags == ["dcat_theme.transporte"]


def test_merge_tag_fqns_is_idempotent():
    assert merge_tag_fqns(["a", "b"], ["b", "c"]) == ["a", "b", "c"]


def test_build_distribution_access_url_is_deterministic():
    assert (
        build_distribution_access_url(
            base_url="https://example.org/datos/poc",
            schema_name="gold",
            table_name="movilidad_resumen_municipio",
        )
        == "https://example.org/datos/poc/gold/movilidad-resumen-municipio"
    )


def test_hvd_category_helpers_support_aliases_and_theme_defaults():
    assert normalize_hvd_category("movilidad") == "http://data.europa.eu/bna/c_b79e35eb"
    assert hvd_category_alias("http://data.europa.eu/bna/c_e1da4e07") == "estadisticas"
    assert normalize_hvd_category("geoespacial") == "http://data.europa.eu/bna/c_ac64a52d"
    assert (
        normalize_hvd_category("observacion_de_la_tierra_y_medio_ambiente")
        == "http://data.europa.eu/bna/c_dd313021"
    )
    assert hvd_category_for_tags(
        tag_fqns=["dcat_theme.transporte"],
        dataset_defaults={"hvd_category_by_theme_tag": {"dcat_theme.transporte": "movilidad"}},
    ) == "http://data.europa.eu/bna/c_b79e35eb"


def test_build_governance_spec_adds_mandatory_hvd_category_when_mapping_exists():
    spec = build_governance_spec(
        schema_name="gold",
        table_name="movilidad_resumen_municipio",
        schema_to_layer={"gold": "Gold"},
        schema_to_domain={},
        tags_by_prefix={"movilidad_": ["dcat_theme.transporte"]},
        catalog_defaults={"publisher_name": "UCLM"},
        dataset_defaults={
            "access_url_base": "https://example.org/datos/poc",
            "hvd_category_by_theme_tag": {"dcat_theme.transporte": "movilidad"},
        },
    )
    assert spec.tag_fqns == ["dcat_theme.transporte"]
    assert spec.custom_properties["dcat_publisher_name"] == "UCLM"
    assert spec.custom_properties["dcat_access_url"] == "https://example.org/datos/poc/gold/movilidad-resumen-municipio"
    assert spec.custom_properties["dcat_hvd_category"] == "http://data.europa.eu/bna/c_b79e35eb"
