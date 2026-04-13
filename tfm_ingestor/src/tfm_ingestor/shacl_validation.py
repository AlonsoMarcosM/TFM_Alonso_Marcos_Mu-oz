from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from rdflib import Graph, Namespace, RDF

from tfm_ingestor.config import DefaultsConfig, RulesConfig
from tfm_ingestor.dcat_export import export_catalog
from tfm_ingestor.om_api import OpenMetadataApi

try:
    from pyshacl import validate as pyshacl_validate
except ImportError as exc:  # pragma: no cover - handled at runtime in CLI
    pyshacl_validate = None  # type: ignore[assignment]
    PYSHACL_IMPORT_ERROR = exc
else:
    PYSHACL_IMPORT_ERROR = None


SH = Namespace("http://www.w3.org/ns/shacl#")
SHACL_BUNDLE_FILENAMES = [
    "shacl_imports.ttl",
    "shacl_mdr_imports.ttl",
    "shacl_common_shapes.ttl",
    "shacl_mdr-vocabularies.shape.ttl",
    "shacl_catalog_shape.ttl",
    "shacl_dataset_shape.ttl",
    "shacl_distribution_shape.ttl",
    "shacl_dataservice_shape.ttl",
]
SHACL_HVD_FILENAMES = [
    "shacl_common_hvd_shapes.ttl",
    "shacl_dataset_hvd_shape.ttl",
    "shacl_distribution_hvd_shape.ttl",
    "shacl_dataservice_hvd_shape.ttl",
]


@dataclass(frozen=True)
class ValidationResultItem:
    severity: str
    focus_node: str | None
    result_path: str | None
    source_shape: str | None
    message: str | None


def bundled_shacl_root_path() -> Path:
    resource = files("tfm_ingestor").joinpath("resources/shacl")
    return Path(str(resource))


def bundled_shacl_manifest_path() -> Path:
    return bundled_shacl_root_path() / "manifest.json"


def bundled_shacl_manifest() -> dict[str, Any]:
    return json.loads(bundled_shacl_manifest_path().read_text(encoding="utf-8"))


def bundled_base_shapes_path() -> Path:
    """Backward-compatible pointer to the frozen official import graph."""
    return bundled_shacl_root_path() / "shacl_imports.ttl"


def bundled_base_shapes_paths() -> list[Path]:
    root = bundled_shacl_root_path()
    return [root / name for name in SHACL_BUNDLE_FILENAMES]


def bundled_dataservice_shape_path() -> Path:
    return bundled_shacl_root_path() / "shacl_dataservice_shape.ttl"


def bundled_hvd_shapes_paths() -> list[Path]:
    base = bundled_shacl_root_path() / "hvd"
    return [base / name for name in SHACL_HVD_FILENAMES]


def _shapes_graph(*, profile_case: str, shapes_path: str | Path | None) -> tuple[Graph, list[str]]:
    graph = Graph()
    loaded_paths: list[str] = []

    if shapes_path is not None:
        effective_path = Path(shapes_path)
        graph.parse(effective_path.resolve().as_uri(), format="turtle")
        return graph, [str(effective_path)]

    for base_path in bundled_base_shapes_paths():
        graph.parse(base_path.resolve().as_uri(), format="turtle")
        loaded_paths.append(str(base_path))

    if profile_case == "hvd":
        for path in bundled_hvd_shapes_paths():
            graph.parse(path.resolve().as_uri(), format="turtle")
            loaded_paths.append(str(path))

    return graph, loaded_paths


def _severity_label(value: Any) -> str:
    if value == SH.Violation:
        return "Violation"
    if value == SH.Warning:
        return "Warning"
    if value == SH.Info:
        return "Info"
    return str(value).rsplit("#", 1)[-1] if value is not None else "Unknown"


def _first_literal(graph: Graph, subject: Any, predicate: Any) -> str | None:
    value = graph.value(subject, predicate)
    if value is None:
        return None
    return str(value)


def _summarize_report(report_graph: Graph) -> tuple[dict[str, int], list[ValidationResultItem]]:
    counts = {"Violation": 0, "Warning": 0, "Info": 0}
    items: list[ValidationResultItem] = []

    for result_node in sorted(set(report_graph.subjects(RDF.type, SH.ValidationResult)), key=str):
        severity_value = report_graph.value(result_node, SH.resultSeverity)
        severity = _severity_label(severity_value)
        if severity not in counts:
            counts[severity] = 0
        counts[severity] += 1
        items.append(
            ValidationResultItem(
                severity=severity,
                focus_node=_first_literal(report_graph, result_node, SH.focusNode),
                result_path=_first_literal(report_graph, result_node, SH.resultPath),
                source_shape=_first_literal(report_graph, result_node, SH.sourceShape),
                message=_first_literal(report_graph, result_node, SH.resultMessage),
            )
        )
    return counts, items


def validate_jsonld_file(
    *,
    input_path: str | Path,
    shapes_path: str | Path | None = None,
    profile_case: str = "hvd",
    allow_warnings: bool = False,
    report_output: str | Path | None = None,
) -> dict[str, Any]:
    if pyshacl_validate is None:
        raise RuntimeError(
            "pyshacl no está instalado. Instala requirements-dev.txt o tfm_ingestor[validation]."
        ) from PYSHACL_IMPORT_ERROR

    input_path = Path(input_path)
    data_graph = Graph()
    data_graph.parse(input_path.resolve().as_uri(), format="json-ld")

    shacl_graph, loaded_shapes = _shapes_graph(profile_case=profile_case, shapes_path=shapes_path)
    bundle_manifest = bundled_shacl_manifest() if shapes_path is None else None

    conforms, report_graph, report_text = pyshacl_validate(
        data_graph,
        shacl_graph=shacl_graph,
        allow_warnings=allow_warnings,
        do_owl_imports=False,
    )

    assert isinstance(report_graph, Graph)
    counts, items = _summarize_report(report_graph)

    if report_output is not None:
        report_graph.serialize(destination=str(report_output), format="turtle")

    return {
        "input_path": str(input_path),
        "profile_case": profile_case,
        "shapes_path": loaded_shapes[0] if len(loaded_shapes) == 1 else None,
        "shapes_paths": loaded_shapes,
        "shacl_bundle": (
            {
                "source_commit": bundle_manifest.get("source_commit"),
                "source_path": bundle_manifest.get("source_path"),
                "frozen_date": bundle_manifest.get("frozen_date"),
                "files": len(bundle_manifest.get("files", [])),
            }
            if bundle_manifest is not None
            else None
        ),
        "allow_warnings": bool(allow_warnings),
        "conforms": bool(conforms),
        "violations": int(counts.get("Violation", 0)),
        "warnings": int(counts.get("Warning", 0)),
        "infos": int(counts.get("Info", 0)),
        "results": [
            {
                "severity": item.severity,
                "focus_node": item.focus_node,
                "result_path": item.result_path,
                "source_shape": item.source_shape,
                "message": item.message,
            }
            for item in items
        ],
        "report_text": report_text,
        "report_output": str(report_output) if report_output is not None else None,
    }


def export_and_validate_catalog(
    *,
    defaults: DefaultsConfig,
    rules: RulesConfig,
    om_api: OpenMetadataApi | None = None,
    limit_tables: int = 1000,
    tables_input: list[dict[str, Any]] | None = None,
    export_output: str | Path | None = None,
    shapes_path: str | Path | None = None,
    profile_case: str = "hvd",
    allow_warnings: bool = False,
    report_output: str | Path | None = None,
) -> dict[str, Any]:
    temp_output: Path | None = None
    if export_output is None:
        with NamedTemporaryFile(prefix="dcat_export_", suffix=".jsonld", delete=False) as tmp:
            temp_output = Path(tmp.name)
        export_target = temp_output
    else:
        export_target = Path(export_output)

    export_summary = export_catalog(
        defaults=defaults,
        rules=rules,
        om_api=om_api,
        limit_tables=limit_tables,
        tables_input=tables_input,
        output_path=str(export_target),
    )
    validation_summary = validate_jsonld_file(
        input_path=export_target,
        shapes_path=shapes_path,
        profile_case=profile_case,
        allow_warnings=allow_warnings,
        report_output=report_output,
    )

    return {
        **export_summary,
        **validation_summary,
        "exported_for_validation": True,
        "export_output": str(export_target),
        "temporary_export": temp_output is not None,
    }
