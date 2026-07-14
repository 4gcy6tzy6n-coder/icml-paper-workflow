from pathlib import Path
from unittest import mock

from paperflow.qa.preview import (
    convert_pptx_to_pdf,
    detect_poppler,
    validate_visual_review,
)


def test_detect_poppler_available() -> None:
    with mock.patch("shutil.which", return_value="/usr/bin/pdftoppm"):
        assert detect_poppler() is True


def test_detect_poppler_missing() -> None:
    with mock.patch("shutil.which", return_value=None):
        assert detect_poppler() is False


def test_convert_pptx_to_pdf_libreoffice_missing(tmp_path: Path) -> None:
    pptx = tmp_path / "slides" / "presentation.pptx"
    pptx.parent.mkdir(parents=True, exist_ok=True)
    pptx.write_bytes(b"fake pptx")

    with mock.patch("shutil.which", return_value=None):
        result = convert_pptx_to_pdf(pptx)
        assert result.success is False
        assert any("LibreOffice" in w for w in result.warnings)


def test_convert_pptx_to_pdf_success(tmp_path: Path) -> None:
    pptx = tmp_path / "slides" / "presentation.pptx"
    pptx.parent.mkdir(parents=True, exist_ok=True)
    pptx.write_bytes(b"fake pptx")

    mock_result = type("CR", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    with mock.patch("shutil.which", return_value="/usr/bin/soffice"), mock.patch(
        "paperflow.qa.preview.run_command", return_value=mock_result
    ):
        pdf = pptx.parent / "presentation.pdf"
        pdf.write_bytes(b"fake pdf")
        result = convert_pptx_to_pdf(pptx)
        assert result.success is True


def test_validate_visual_review_requires_final_pass() -> None:

    review = {
        "schema_version": "1.0",
        "inspection_pass": 1,
        "reviewed_slide_count": 15,
        "issues": [],
        "fixes_applied": [],
        "rerendered": False,
        "final_pass": False,
    }
    issues = validate_visual_review(review, 15)
    codes = {i.code for i in issues}
    assert "VISUAL_FINAL_PASS_REQUIRED" in codes


def test_validate_visual_review_passes() -> None:
    review = {
        "schema_version": "1.0",
        "inspection_pass": 1,
        "reviewed_slide_count": 15,
        "issues": [],
        "fixes_applied": [{"slide_id": "slide-07", "issue_type": "text_overflow"}],
        "rerendered": True,
        "final_pass": True,
    }
    issues = validate_visual_review(review, 15)
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0
