from tfm_ingestor.patch_ops import build_table_patch_ops


def test_build_table_patch_ops_prunes_managed_tags_and_custom_properties():
    table = {
        "tags": [
            {"tagFQN": "dcat_theme.transport"},
            {"tagFQN": "dcat_keyword.bici"},
            {"tagFQN": "classification.other"},
        ],
        "extension": {
            "dcat_publisher_name": "Legacy",
            "dcat_hvd_category": "http://data.europa.eu/bna/c_e1da4e07",
            "dcat_contact_email": "legacy@example.org",
            "dct_license": "CC-BY-4.0",
            "dcat_access_url": "https://example.org/data.csv",
            "tfm_layer": "Bronze",
            "other_field": "keep-me",
        },
    }

    ops = build_table_patch_ops(
        table=table,
        desired_tag_fqns=["dcat_theme.transporte"],
        desired_custom_properties={
            "dcat_publisher_name": "UCLM",
            "dcat_hvd_category": "http://data.europa.eu/bna/c_b79e35eb",
        },
        managed_tag_prefixes=["dcat_theme.", "dcat_keyword."],
        managed_custom_property_keys=[
            "dcat_publisher_name",
            "dcat_hvd_category",
            "dcat_contact_email",
            "dct_license",
            "dcat_access_url",
            "tfm_layer",
        ],
    )

    tags_op = next(op for op in ops if op["path"] == "/tags")
    assert tags_op["value"] == [
        {"tagFQN": "classification.other", "labelType": "Manual", "state": "Confirmed"},
        {"tagFQN": "dcat_theme.transporte", "labelType": "Manual", "state": "Confirmed"},
    ]

    extension_op = next(op for op in ops if op["path"] == "/extension")
    assert extension_op["value"] == {
        "other_field": "keep-me",
        "dcat_publisher_name": "UCLM",
        "dcat_hvd_category": "http://data.europa.eu/bna/c_b79e35eb",
    }
