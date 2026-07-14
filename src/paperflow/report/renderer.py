import shutil
from pathlib import Path

from paperflow.models.qa import RenderResult
from paperflow.util.commands import run_command


def detect_quarto() -> bool:
    return shutil.which("quarto") is not None


def detect_libreoffice() -> bool:
    return shutil.which("soffice") is not None


def render_docx(qmd_path: Path) -> RenderResult:
    """Render a QMD file to DOCX using Quarto."""
    if not detect_quarto():
        return RenderResult(
            success=False,
            warnings=[
                "Quarto is not installed. Install it from https://quarto.org/docs/download/ "
                "or run: brew install quarto"
            ],
        )

    report_dir = qmd_path.parent
    result = run_command(
        ["quarto", "render", qmd_path.name, "--to", "docx"],
        cwd=report_dir,
        timeout_s=120,
    )

    if result.returncode != 0:
        return RenderResult(
            success=False,
            warnings=[f"Quarto render failed: {result.stderr}"],
        )

    docx_path = report_dir / "academic-report.docx"
    return RenderResult(
        success=True,
        output_paths=[str(docx_path)] if docx_path.exists() else [],
    )


def render_pdf_via_libreoffice(docx_path: Path) -> RenderResult:
    """Convert a DOCX file to PDF using LibreOffice."""
    if not detect_libreoffice():
        return RenderResult(
            success=False,
            warnings=[
                "LibreOffice is not installed. Install it from https://www.libreoffice.org/ "
                "or run: brew install libreoffice"
            ],
        )

    out_dir = docx_path.parent
    result = run_command(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir",
         str(out_dir), str(docx_path)],
        timeout_s=120,
    )

    if result.returncode != 0:
        return RenderResult(
            success=False,
            warnings=[f"LibreOffice conversion failed: {result.stderr}"],
        )

    pdf_path = out_dir / "academic-report.pdf"
    return RenderResult(
        success=True,
        output_paths=[str(pdf_path)] if pdf_path.exists() else [],
    )


def render_report(workspace: Path) -> RenderResult:
    """Render the full report (QMD → DOCX → PDF)."""
    qmd_path = workspace / "report" / "academic-report.qmd"
    if not qmd_path.exists():
        return RenderResult(
            success=False,
            warnings=[f"Report QMD not found: {qmd_path}"],
        )

    docx_result = render_docx(qmd_path)
    if not docx_result.success:
        return docx_result

    docx_path = workspace / "report" / "academic-report.docx"
    pdf_result = render_pdf_via_libreoffice(docx_path)
    if not pdf_result.success:
        warnings = list(docx_result.warnings) + list(pdf_result.warnings)
        return RenderResult(
            success=True,
            output_paths=list(docx_result.output_paths),
            warnings=warnings,
        )

    return RenderResult(
        success=True,
        output_paths=list(docx_result.output_paths) + list(pdf_result.output_paths),
    )
