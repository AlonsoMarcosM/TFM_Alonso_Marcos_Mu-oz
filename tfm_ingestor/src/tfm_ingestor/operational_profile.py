from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping at top-level: {path}")
    return data


def _resolve_path(*, raw_value: Any, repo_root: Path, fallback: Path) -> Path:
    if raw_value is None or str(raw_value).strip() == "":
        return fallback
    path = Path(str(raw_value))
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


@dataclass(frozen=True)
class OperationalWorkflowDefaults:
    profile_case: str = "hvd"
    allow_warnings: bool = False
    refresh_sheet: bool = True
    export_output: str = "dcat_catalog.jsonld"
    report_output: str | None = None


@dataclass(frozen=True)
class OperationalProfile:
    path: Path
    defaults_path: Path
    rules_path: Path
    sheet_path: Path
    workflow: OperationalWorkflowDefaults


def load_operational_profile(path: str | Path, *, repo_root: Path, defaults_path: Path, rules_path: Path, sheet_path: Path) -> OperationalProfile:
    profile_path = Path(path).resolve()
    raw = _load_yaml(profile_path)

    workflow_raw = raw.get("workflow", {}) or {}
    if not isinstance(workflow_raw, dict):
        raise ValueError(f"Invalid 'workflow' block in {profile_path}")

    profile_case = str(workflow_raw.get("profile_case") or "hvd").strip().lower()
    if profile_case not in {"base", "hvd"}:
        raise ValueError(f"Invalid workflow.profile_case in {profile_path}: {profile_case!r}")

    allow_warnings = workflow_raw.get("allow_warnings", False)
    refresh_sheet = workflow_raw.get("refresh_sheet", True)
    if not isinstance(allow_warnings, bool):
        raise ValueError(f"Invalid workflow.allow_warnings in {profile_path} (must be bool)")
    if not isinstance(refresh_sheet, bool):
        raise ValueError(f"Invalid workflow.refresh_sheet in {profile_path} (must be bool)")

    report_output_raw = workflow_raw.get("report_output")
    report_output = None if report_output_raw is None or str(report_output_raw).strip() == "" else str(report_output_raw)

    return OperationalProfile(
        path=profile_path,
        defaults_path=_resolve_path(raw_value=raw.get("defaults_path"), repo_root=repo_root, fallback=defaults_path),
        rules_path=_resolve_path(raw_value=raw.get("rules_path"), repo_root=repo_root, fallback=rules_path),
        sheet_path=_resolve_path(raw_value=raw.get("sheet_path"), repo_root=repo_root, fallback=sheet_path),
        workflow=OperationalWorkflowDefaults(
            profile_case=profile_case,
            allow_warnings=allow_warnings,
            refresh_sheet=refresh_sheet,
            export_output=str(workflow_raw.get("export_output") or "dcat_catalog.jsonld"),
            report_output=report_output,
        ),
    )
