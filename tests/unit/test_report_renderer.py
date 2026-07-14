from pathlib import Path
from unittest import mock

from paperflow.report.renderer import (
    detect_libreoffice,
    detect_quarto,
    render_docx,
    render_report,
)


def test_detect_quarto_available() -> None:
    with mock.patch("shutil.which", return_value="/usr/local/bin/quarto"):
        assert detect_quarto() is True


def test_detect_quarto_missing() -> None:
    with mock.patch("shutil.which", return_value=None):
        assert detect_quarto() is False


def test_detect_libreoffice_available() -> None:
    with mock.patch("shutil.which", return_value="/usr/bin/soffice"):
        assert detect_libreoffice() is True


def test_render_docx_quarto_missing(tmp_path: Path) -> None:
    qmd = tmp_path / "report.qmd"
    qmd.write_text("# Test\n", encoding="utf-8")
    with mock.patch("shutil.which", return_value=None):
        result = render_docx(qmd)
        assert result.success is False
        assert any("Quarto" in w for w in result.warnings)


def test_render_docx_success(tmp_path: Path) -> None:
    qmd = tmp_path / "report.qmd"
    qmd.write_text("# Test\n", encoding="utf-8")

    mock_result = type("CR", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    with mock.patch("shutil.which", return_value="/usr/bin/quarto"), mock.patch(
        "paperflow.report.renderer.run_command", return_value=mock_result
    ):
        result = render_docx(qmd)
        assert result.success is True


def test_render_report_qmd_missing(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "report").mkdir()
    result = render_report(ws)
    assert result.success is False
