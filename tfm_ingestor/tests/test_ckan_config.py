from pathlib import Path

import pytest

from tfm_ingestor.config import load_ckan_harvest


def test_load_ckan_harvest_requires_dataset_mapping(tmp_path: Path):
    p = tmp_path / "ckan.yaml"
    p.write_text(
        "\n".join(
            [
                "ckan:",
                "  base_url: https://demo.ckan.org",
                "mapping: {}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_ckan_harvest(p)


def test_load_ckan_harvest_parses_minimal_config(tmp_path: Path):
    p = tmp_path / "ckan.yaml"
    p.write_text(
        "\n".join(
            [
                "ckan:",
                "  base_url: https://demo.ckan.org",
                "mapping:",
                "  dataset_to_table_fqn:",
                "    bici-uso: postgres_demo_service.opendata_demo.bronze.bici_uso_raw",
                "",
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_ckan_harvest(p)
    assert cfg.ckan.base_url == "https://demo.ckan.org"
    assert cfg.ckan.fallback_base_urls == []
    assert cfg.ckan.rows == 100
    assert cfg.ckan.max_datasets is None
    assert cfg.dataset_to_table_fqn["bici-uso"].endswith("bici_uso_raw")
