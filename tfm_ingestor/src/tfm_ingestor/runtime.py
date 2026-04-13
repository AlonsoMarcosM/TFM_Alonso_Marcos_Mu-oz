from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    defaults_path: Path
    rules_path: Path
    sheet_path: Path
    harvest_config_path: Path
    operational_profile_path: Path
    sql_demo_path: Path


def repo_paths() -> RepoPaths:
    root = Path(__file__).resolve().parents[3]
    return RepoPaths(
        repo_root=root,
        defaults_path=root / "tfm_ingestor" / "config" / "governance_defaults.yaml",
        rules_path=root / "tfm_ingestor" / "config" / "mapping_rules.yaml",
        sheet_path=root / "tfm_ingestor" / "config" / "gold_governance.csv",
        harvest_config_path=root / "tfm_ingestor" / "config" / "ckan_harvest.yaml",
        operational_profile_path=root / "tfm_ingestor" / "config" / "operational_profile.yaml",
        sql_demo_path=root / "sql" / "opendata_demo_init.sql",
    )
