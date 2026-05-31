from pathlib import Path

from tfm_ingestor.operational_profile import load_operational_profile


def test_load_operational_profile_resolves_repo_relative_paths(tmp_path: Path):
    repo_root = tmp_path / "repo"
    profile_path = repo_root / "tfm_ingestor" / "config" / "operational_profile.yaml"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(
        "\n".join(
            [
                'defaults_path: "tfm_ingestor/config/governance_defaults.yaml"',
                'rules_path: "tfm_ingestor/config/mapping_rules.yaml"',
                'sheet_path: "tfm_ingestor/config/gold_governance.csv"',
                "workflow:",
                '  profile_case: "hvd"',
                "  allow_warnings: true",
                "  refresh_sheet: false",
                '  export_output: "tmp/catalog.jsonld"',
                '  report_output: "tmp/report.ttl"',
            ]
        ),
        encoding="utf-8",
    )

    profile = load_operational_profile(
        profile_path,
        repo_root=repo_root,
        defaults_path=repo_root / "defaults-fallback.yaml",
        rules_path=repo_root / "rules-fallback.yaml",
        sheet_path=repo_root / "sheet-fallback.csv",
    )

    assert profile.defaults_path == repo_root / "tfm_ingestor" / "config" / "governance_defaults.yaml"
    assert profile.rules_path == repo_root / "tfm_ingestor" / "config" / "mapping_rules.yaml"
    assert profile.sheet_path == repo_root / "tfm_ingestor" / "config" / "gold_governance.csv"
    assert profile.workflow.profile_case == "hvd"
    assert profile.workflow.allow_warnings is True
    assert profile.workflow.refresh_sheet is False
    assert profile.workflow.export_output == "tmp/catalog.jsonld"
    assert profile.workflow.report_output == "tmp/report.ttl"
