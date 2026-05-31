from pathlib import Path

import pytest

from tfm_ingestor.main import cli_validate_governance_sheet


def test_cli_validate_governance_sheet_reports_valid_sheet(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    path = tmp_path / "sheet.csv"
    path.write_text(
        "\n".join(
            [
                "publicar;schema_name;table_name;table_fqn;titulo_dataset;descripcion_dataset;publicador;tematica_dcat;categoria_hvd;access_url_distribucion",
                "si;gold;movilidad_resumen_municipio;svc.db.gold.movilidad_resumen_municipio;Movilidad;Descripcion;UCLM;transporte;movilidad;https://example.org/datos/plataforma-gobierno-dato/gold/movilidad",
            ]
        ),
        encoding="utf-8-sig",
    )

    assert cli_validate_governance_sheet(["--sheet", str(path)]) == 0
    output = capsys.readouterr().out
    assert '"conforms": true' in output
    assert '"row_count": 1' in output


def test_cli_validate_governance_sheet_reports_invalid_sheet(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    path = tmp_path / "sheet.csv"
    path.write_text(
        "\n".join(
            [
                "publicar;schema_name;table_name;table_fqn;titulo_dataset;descripcion_dataset;publicador;tematica_dcat;categoria_hvd;access_url_distribucion",
                "si;gold;movilidad_resumen_municipio;svc.db.gold.movilidad_resumen_municipio;Movilidad;;;;movilidad;https://example.org/datos/plataforma-gobierno-dato/gold/movilidad",
            ]
        ),
        encoding="utf-8-sig",
    )

    assert cli_validate_governance_sheet(["--sheet", str(path)]) == 2
    output = capsys.readouterr().out
    assert '"conforms": false' in output
    assert "descripcion_dataset" in output
