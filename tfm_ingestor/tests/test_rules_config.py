import textwrap
from pathlib import Path

import pytest

from tfm_ingestor.config import load_defaults, load_rules


def test_load_defaults_requires_catalog_keys(tmp_path: Path):
    p = tmp_path / "defaults.yaml"
    p.write_text("catalog: {}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_defaults(p)


def test_load_rules_requires_mandatory_sections(tmp_path: Path):
    p = tmp_path / "rules.yaml"
    p.write_text("schema_to_layer: {}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_rules(p)


def test_load_rules_normalizes_tags(tmp_path: Path):
    p = tmp_path / "rules.yaml"
    p.write_text(
        textwrap.dedent(
            """
            schema_to_layer:
              bronze: Bronze
            schema_to_domain:
              bronze: OpenData_Bronze
            table_tags_by_prefix:
              bici_: ["a", "b"]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    rules = load_rules(p)
    assert rules.table_tags_by_prefix["bici_"] == ["a", "b"]

