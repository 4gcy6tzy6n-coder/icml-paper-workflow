import shutil
from pathlib import Path
from typing import Any

from paperflow.models.common import Severity
from paperflow.models.qa import RenderResult, ValidationIssue
from paperflow.util.commands import run_command


def detect_libreoffice() -> bool:
    return shutil.which("soffice") is not None


def detect_poppler() -> bool:
    return shutil.which("pdftoppm") is not None


def convert_pptx_to_pdf(pptx_path: Path) -> RenderResult:
    """Convert PPTX to PDF using LibreOffice headless mode."""
    if not detect_libreoffice():
        return RenderResult(
            success=False,
            warnings=[
                "LibreOffice is not installed. Install it from "
                "https://www.libreoffice.org/ or run: brew install libreoffice"
            ],
        )
    out_dir = pptx_path.parent
    result = run_command(
        ["soffice", "--headless", "--convert-to", "pdf",
         "--outdir", str(out_dir), str(pptx_path)],
        timeout_s=120,
    )
    if result.returncode != 0:
        return RenderResult(
            success=False,
            warnings=[f"LibreOffice conversion failed: {result.stderr}"],
        )
    pdf_path = out_dir / "presentation.pdf"
    if pdf_path.exists():
        return RenderResult(success=True, output_paths=[str(pdf_path)])
    return RenderResult(
        success=False,
        warnings=["PDF was not created after conversion."],
    )


def rasterize_pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int = 150) -> RenderResult:
    """Convert PDF pages to PNG images using pdftoppm."""
    if not detect_poppler():
        return RenderResult(
            success=False,
            warnings=[
                "Poppler (pdftoppm) is not installed. Install it from "
                "https://poppler.freedesktop.org/ or run: brew install poppler"
            ],
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    result = run_command(
        ["pdftoppm", "-png", "-r", str(dpi), str(pdf_path),
         str(output_dir / "slide")],
        timeout_s=120,
    )
    if result.returncode != 0:
        return RenderResult(
            success=False,
            warnings=[f"pdftoppm failed: {result.stderr}"],
        )

    images = sorted(output_dir.glob("slide-*.png"))
    renamed: list[str] = []
    for i, img in enumerate(images):
        new_name = output_dir / f"slide-{i + 1:03d}.png"
        img.rename(new_name)
        renamed.append(str(new_name))

    return RenderResult(
        success=len(renamed) > 0,
        output_paths=renamed,
    )


def create_contact_sheet(image_dir: Path, output_path: Path) -> RenderResult:
    """Create a contact sheet grid from slide images using Pillow."""
    try:
        from PIL import Image
    except ImportError:
        return RenderResult(
            success=False,
            warnings=["Pillow is required for contact sheet generation."],
        )

    images = sorted(image_dir.glob("slide-*.png"))
    if not images:
        return RenderResult(
            success=False,
            warnings=["No slide images found for contact sheet."],
        )

    cols = min(5, len(images))
    rows = (len(images) + cols - 1) // cols

    thumb_w, thumb_h = 300, 169
    sheet = Image.new("RGB", (cols * thumb_w + 20, rows * thumb_h + 20), "white")

    for i, img_path in enumerate(images):
        img = Image.open(img_path)
        img.thumbnail((thumb_w, thumb_h))
        row, col = divmod(i, cols)
        x, y = 10 + col * thumb_w, 10 + row * thumb_h
        sheet.paste(img, (x, y))

    sheet.save(str(output_path))
    return RenderResult(success=True, output_paths=[str(output_path)])


def validate_visual_review(
    review: dict[str, Any], total_slides: int
) -> list[ValidationIssue]:
    """Validate a visual review JSON against mandatory rules."""
    issues: list[ValidationIssue] = []

    if not review.get("final_pass"):
        issues.append(
            ValidationIssue(
                code="VISUAL_FINAL_PASS_REQUIRED",
                severity=Severity.ERROR,
                message="Final pass must be marked as complete.",
            )
        )

    if not review.get("rerendered"):
        issues.append(
            ValidationIssue(
                code="VISUAL_RERENDER_REQUIRED",
                severity=Severity.ERROR,
                message="At least one re-render cycle is required before final pass.",
            )
        )

    inspection_pass = review.get("inspection_pass", 0)
    if inspection_pass < 1:
        issues.append(
            ValidationIssue(
                code="VISUAL_INSPECTION_REQUIRED",
                severity=Severity.ERROR,
                message="At least one inspection pass is required.",
            )
        )

    reviewed = review.get("reviewed_slide_count", 0)
    if reviewed < total_slides:
        issues.append(
            ValidationIssue(
                code="VISUAL_INCOMPLETE_REVIEW",
                severity=Severity.ERROR,
                message=f"Only {reviewed}/{total_slides} slides reviewed.",
            )
        )

    for issue in review.get("issues", []):
        if issue.get("severity") == "error":
            issues.append(
                ValidationIssue(
                    code="VISUAL_UNRESOLVED_ERROR",
                    severity=Severity.ERROR,
                    message=f"Unresolved issue on {issue.get('slide_id', 'unknown')}: "
                    f"{issue.get('description', '')}",
                )
            )

    return issues
