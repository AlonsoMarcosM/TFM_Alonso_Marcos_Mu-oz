from __future__ import annotations

import json

import pytest

from tfm_ingestor.report_render import (
    _collect_status,
    _flatten,
    render_html,
    render_validation_report,
)


def _sample() -> dict:
    return {
        "runtime_validation": {"conforms": True, "technical": {"conforms": True}},
        "idempotence": {"conforms": False, "second_applied": 1},
        "second_workflow": {"validation": {"conforms": True, "warnings": 3}},
        "notas": ["catálogo válido", "sin violaciones bloqueantes"],
    }


def test_collect_status_finds_nested_flags():
    status = dict(_collect_status(_sample()))
    assert status["runtime_validation.conforms"] is True
    assert status["idempotence.conforms"] is False
    assert status["second_workflow.validation.conforms"] is True


def test_flatten_renders_scalars_and_lists():
    flat = dict(_flatten(_sample()))
    assert flat["idempotence.second_applied"] == "1"
    assert flat["second_workflow.validation.conforms"] == "sí"
    assert flat["notas"] == "catálogo válido, sin violaciones bloqueantes"


def test_render_html_marks_conformance(tmp_path):
    out = tmp_path / "report.html"
    render_html(_sample(), str(out), title="Informe", source="v.json")
    html = out.read_text(encoding="utf-8")
    assert out.stat().st_size > 0
    assert "CONFORME" in html
    assert "NO CONFORME" in html
    # acentos preservados (UTF-8)
    assert "catálogo válido" in html


def test_render_validation_report_html_only(tmp_path):
    src = tmp_path / "v.json"
    src.write_text(json.dumps(_sample(), ensure_ascii=False), encoding="utf-8")
    out_html = tmp_path / "v.html"
    result = render_validation_report(str(src), html_output=str(out_html))
    assert result["html_output"] == str(out_html)
    assert result["pdf_output"] is None
    assert out_html.exists()


def test_render_pdf_produces_valid_file(tmp_path):
    pytest.importorskip("fpdf")
    src = tmp_path / "v.json"
    src.write_text(json.dumps(_sample(), ensure_ascii=False), encoding="utf-8")
    out_pdf = tmp_path / "v.pdf"
    result = render_validation_report(str(src), pdf_output=str(out_pdf))
    assert result["pdf_output"] == str(out_pdf)
    assert out_pdf.exists()
    assert out_pdf.read_bytes()[:4] == b"%PDF"
