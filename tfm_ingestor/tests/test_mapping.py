from tfm_ingestor.mapping import (
    domain_for_schema,
    layer_for_schema,
    merge_tag_fqns,
    tags_for_table,
)


def test_layer_for_schema():
    m = {"bronze": "Bronze"}
    assert layer_for_schema("bronze", m) == "Bronze"
    assert layer_for_schema("silver", m) is None


def test_domain_for_schema():
    m = {"bronze": "OpenData_Bronze"}
    assert domain_for_schema("bronze", m) == "OpenData_Bronze"
    assert domain_for_schema("silver", m) is None


def test_tags_for_table_prefixes_are_applied_and_deduped():
    rules = {"bici_": ["dcat_theme.transport", "dcat_keyword.bici"], "bici_uso": ["dcat_keyword.bici"]}
    tags = tags_for_table("bici_uso_raw", rules)
    assert tags == ["dcat_theme.transport", "dcat_keyword.bici"]


def test_merge_tag_fqns_is_idempotent():
    assert merge_tag_fqns(["a", "b"], ["b", "c"]) == ["a", "b", "c"]

