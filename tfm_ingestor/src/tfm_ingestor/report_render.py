"""Render validation report artifacts (HTML and PDF) from a validation JSON.

This module turns the JSON produced by the validation flow
(``validate-runtime``, ``workflow run`` or ``run_validation_suite.ps1``) into
two human-readable artifacts:

* an HTML report, generated with the standard library only, so it always works;
* a PDF report, generated with ``fpdf2`` (pure Python, cross-platform).

The renderer is intentionally generic: it walks an arbitrary JSON object,
highlights conformance/status flags and flattens the rest into a readable
key/value listing. The same code therefore serves the runtime report, the
SHACL summary and the full validation suite summary.
"""

from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

DEFAULT_TITLE = "Informe de validación — Plataforma de Gobierno del Dato"

# Keys whose boolean value represents a pass/fail status.
_STATUS_EXACT = {
    "conforms",
    "conformant",
    "ok",
    "passed",
    "valid",
    "success",
    "idempotence",
}


def _is_status_key(key: str) -> bool:
    k = str(key).lower()
    return k in _STATUS_EXACT or k.endswith("_conforms") or k.endswith("conforms")


def _status_text(value: bool) -> str:
    return "CONFORME" if value else "NO CONFORME"


def load_report(input_path: str) -> dict[str, Any]:
    """Load a validation JSON file, always returning a dict.

    Uses ``utf-8-sig`` so a UTF-8 BOM (written by ``Set-Content -Encoding utf8``
    on Windows PowerShell) is stripped transparently instead of breaking the
    JSON parser.
    """
    data = json.loads(Path(input_path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        return {"valor": data}
    return data


def _collect_status(data: Any, prefix: str = "") -> list[tuple[str, bool]]:
    """Collect (path, bool) pairs for keys that represent a status flag."""
    found: list[tuple[str, bool]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, bool) and _is_status_key(key):
                found.append((path, value))
            elif isinstance(value, (dict, list)):
                found.extend(_collect_status(value, path))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            found.extend(_collect_status(value, f"{prefix}[{index}]"))
    return found


def _flatten(data: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten a nested JSON object into ordered (path, value) string rows."""
    rows: list[tuple[str, str]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten(value, path))
    elif isinstance(data, list):
        if not data:
            rows.append((prefix, "(vacío)"))
        elif all(not isinstance(item, (dict, list)) for item in data):
            rows.append((prefix, ", ".join(str(item) for item in data)))
        else:
            for index, value in enumerate(data):
                rows.extend(_flatten(value, f"{prefix}[{index}]"))
    else:
        if isinstance(data, bool):
            text = "sí" if data else "no"
        elif data is None:
            text = "(sin valor)"
        else:
            text = str(data)
        rows.append((prefix or "valor", text))
    return rows


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --tema: #2b6cb0; --ok: #2f855a; --ko: #c53030; --bg: #f6f6f8; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "Segoe UI", Arial, sans-serif; color: #1a202c; margin: 0; padding: 2rem; background: #fff; }}
  header {{ border-bottom: 3px solid var(--tema); padding-bottom: 1rem; margin-bottom: 1.5rem; }}
  h1 {{ color: var(--tema); font-size: 1.5rem; margin: 0 0 .3rem; }}
  .meta {{ color: #4a5568; font-size: .85rem; }}
  h2 {{ color: var(--tema); font-size: 1.1rem; margin-top: 2rem; border-bottom: 1px solid #e2e8f0; padding-bottom: .3rem; }}
  .badges {{ display: flex; flex-wrap: wrap; gap: .6rem; margin: 1rem 0; }}
  .badge {{ border-radius: 6px; padding: .4rem .7rem; font-size: .85rem; font-weight: 600; color: #fff; }}
  .badge .k {{ font-weight: 400; opacity: .9; display: block; font-size: .72rem; }}
  .ok {{ background: var(--ok); }}
  .ko {{ background: var(--ko); }}
  table {{ border-collapse: collapse; width: 100%; font-size: .82rem; }}
  th, td {{ text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
  th {{ background: var(--bg); width: 45%; font-family: Consolas, monospace; font-weight: 600; color: #2d3748; }}
  td {{ word-break: break-word; }}
  footer {{ margin-top: 2.5rem; color: #718096; font-size: .75rem; border-top: 1px solid #e2e8f0; padding-top: .8rem; }}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <div class="meta">Fuente: <code>{source}</code><br>Generado: {generated_at}</div>
</header>
{badges_section}
<h2>Detalle</h2>
<table>
<tbody>
{rows}
</tbody>
</table>
<footer>Informe generado automáticamente por <code>om_dcat_sync render-report</code> a partir del JSON de validación. Plataforma de Gobierno del Dato.</footer>
</body>
</html>
"""


def render_html(data: dict[str, Any], output_path: str, *, title: str, source: str) -> str:
    generated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    status = _collect_status(data)
    if status:
        badges = "".join(
            '<div class="badge {cls}"><span class="k">{path}</span>{label}</div>'.format(
                cls="ok" if value else "ko",
                path=html.escape(path),
                label=_status_text(value),
            )
            for path, value in status
        )
        badges_section = f'<h2>Resumen de conformidad</h2>\n<div class="badges">{badges}</div>'
    else:
        badges_section = ""

    rows = "\n".join(
        "<tr><th>{key}</th><td>{value}</td></tr>".format(
            key=html.escape(key), value=html.escape(value)
        )
        for key, value in _flatten(data)
    )

    document = _HTML_TEMPLATE.format(
        title=html.escape(title),
        source=html.escape(source),
        generated_at=generated_at,
        badges_section=badges_section,
        rows=rows,
    )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(document, encoding="utf-8")
    return str(out)


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _latin1(text: str) -> str:
    """fpdf2 core fonts use latin-1; keep Spanish accents, replace the rest."""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def render_pdf(data: dict[str, Any], output_path: str, *, title: str, source: str) -> str:
    try:
        from fpdf import FPDF  # type: ignore
        from fpdf.enums import XPos, YPos  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "La generación de PDF requiere 'fpdf2'. Instálalo con "
            "'python -m pip install fpdf2' o reinstala el paquete con el extra [report]."
        ) from exc

    generated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    def line(text: str, *, height: float, style: str = "", size: float = 9,
             color: tuple[int, int, int] = (26, 32, 44)) -> None:
        # Reset x to the left margin so multi_cell(w=0) always uses the full
        # printable width; wrapmode CHAR then breaks long unbreakable tokens
        # (paths, FQNs) without entering a degenerate zero-width loop.
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, height, _latin1(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT, wrapmode="CHAR")

    line(title, height=8, style="B", size=15, color=(43, 108, 176))
    line(f"Fuente: {source}", height=5, size=9, color=(74, 85, 104))
    line(f"Generado: {generated_at}", height=5, size=9, color=(74, 85, 104))
    pdf.ln(2)

    status = _collect_status(data)
    if status:
        line("Resumen de conformidad", height=7, style="B", size=12, color=(43, 108, 176))
        for path, value in status:
            label = f"{path}: {_status_text(value)}"
            line(label, height=5, style="B", size=10,
                 color=(47, 133, 90) if value else (197, 48, 48))
        pdf.ln(2)

    line("Detalle", height=7, style="B", size=12, color=(43, 108, 176))
    pdf.ln(1)
    for key, value in _flatten(data):
        line(key, height=4.5, style="B", size=8, color=(45, 55, 72))
        line(value, height=5, size=9, color=(26, 32, 44))
        pdf.ln(0.5)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    return str(out)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def render_validation_report(
    input_path: str,
    *,
    html_output: str | None = None,
    pdf_output: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Render HTML and/or PDF from a validation JSON file.

    If neither output is given, both are derived from ``input_path`` (same
    stem with ``.html`` and ``.pdf`` extensions).
    """
    src = Path(input_path)
    if html_output is None and pdf_output is None:
        html_output = str(src.with_suffix(".html"))
        pdf_output = str(src.with_suffix(".pdf"))

    data = load_report(input_path)
    report_title = title or DEFAULT_TITLE

    result: dict[str, Any] = {
        "input": str(src),
        "title": report_title,
        "html_output": None,
        "pdf_output": None,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
    }

    if html_output:
        result["html_output"] = render_html(
            data, html_output, title=report_title, source=str(src)
        )
    if pdf_output:
        result["pdf_output"] = render_pdf(
            data, pdf_output, title=report_title, source=str(src)
        )
    return result
