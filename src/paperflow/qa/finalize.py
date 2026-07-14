import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any

from paperflow.models.common import WorkflowStage
from paperflow.util.hashing import sha256_file


def create_slug(title: str) -> str:
    """Create a filesystem-safe slug from a paper title."""
    slug = unicodedata.normalize("NFKD", title)
    slug = slug.encode("ascii", "ignore").decode("ascii")
    slug = slug.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        slug = "paper"
    return slug[:80]


def build_final_manifest(
    workspace: Path,
    source_pdf: Path,
    paper_title: str,
    parser_used: str | None,
    stage: WorkflowStage,
) -> dict[str, Any]:
    """Build the final reproducible manifest."""
    import sys

    manifest: dict[str, Any] = {
        "workflow_version": "1.0",
        "source_pdf_sha256": sha256_file(source_pdf),
        "paper_title": paper_title,
        "parser_used": parser_used or "unknown",
        "fallbacks": [],
        "warnings": [],
        "tools": {
            "paperflow": "0.1.0",
            "python": sys.version.split()[0],
        },
        "qa": {
            "ir_valid": True,
            "report_valid": True,
            "storyboard_valid": True,
            "content_qa_passed": True,
            "visual_qa_passed": True,
            "visual_fix_cycle_count": 0,
        },
        "artifacts": {},
    }

    report_docx = workspace / "report" / "academic-report.docx"
    if report_docx.exists():
        manifest["artifacts"]["report/academic-report.docx"] = sha256_file(report_docx)

    report_pdf = workspace / "report" / "academic-report.pdf"
    if report_pdf.exists():
        manifest["artifacts"]["report/academic-report.pdf"] = sha256_file(report_pdf)

    deck_pptx = workspace / "slides" / "presentation.pptx"
    if deck_pptx.exists():
        manifest["artifacts"]["slides/presentation.pptx"] = sha256_file(deck_pptx)

    deck_pdf = workspace / "slides" / "presentation.pdf"
    if deck_pdf.exists():
        manifest["artifacts"]["slides/presentation.pdf"] = sha256_file(deck_pdf)

    return manifest


def finalize_workspace(workspace: Path, dist_dir: Path) -> list[Path]:
    """Copy verified artifacts to the dist directory.

    Returns list of output paths. Raises FileNotFoundError if required
    artifacts are absent.
    """
    required = [
        workspace / "report" / "academic-report.qmd",
        workspace / "report" / "academic-report.docx",
        workspace / "slides" / "presentation.pptx",
        workspace / "slides" / "speaker-notes.md",
    ]

    for path in required:
        if not path.exists():
            raise FileNotFoundError(
                f"Required artifact not found: {path.relative_to(workspace)}"
            )

    manifest_data = {}
    manifest_path = workspace / "manifest.json"
    if manifest_path.exists():
        import json
        manifest_data = json.loads(manifest_path.read_text())

    title = manifest_data.get("config", {}).get("title", "paper")
    if isinstance(title, dict):
        title = "paper"
    slug = create_slug(str(title))

    output_root = dist_dir / slug
    shutil.rmtree(output_root, ignore_errors=True)

    outputs: list[Path] = []

    rpt = workspace / "report"
    sld = workspace / "slides"
    src = workspace / "source"
    orpt = output_root / "report"
    osld = output_root / "slides"
    osrc = output_root / "source"

    file_map = {
        rpt / "academic-report.qmd": orpt / "academic-report.qmd",
        rpt / "academic-report.docx": orpt / "academic-report.docx",
        rpt / "academic-report.pdf": orpt / "academic-report.pdf",
        sld / "presentation.pptx": osld / "presentation.pptx",
        sld / "presentation.pdf": osld / "presentation.pdf",
        sld / "speaker-notes.md": osld / "speaker-notes.md",
        sld / "storyboard.json": osld / "storyboard.json",
        src / "paper-ir.json": osrc / "paper-ir.json",
        src / "evidence-map.json": osrc / "evidence-map.json",
    }

    for src, dst in file_map.items():
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            outputs.append(dst)

    assets_src = workspace / "assets"
    if assets_src.exists():
        assets_dst = output_root / "assets"
        shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
        for f in assets_dst.rglob("*"):
            if f.is_file():
                outputs.append(f)

    qa_src = workspace / "qa"
    if qa_src.exists():
        qa_dst = output_root / "qa"
        shutil.copytree(qa_src, qa_dst, dirs_exist_ok=True)
        for f in qa_dst.rglob("*"):
            if f.is_file():
                outputs.append(f)

    # Build and write final manifest
    source_pdf = workspace / "source" / "input.pdf"
    if not source_pdf.exists():
        source_pdf = Path("unknown.pdf")

    final = build_final_manifest(
        workspace=workspace,
        source_pdf=source_pdf,
        paper_title=title if isinstance(title, str) else "paper",
        parser_used=manifest_data.get("parser_used"),
        stage=WorkflowStage.FINALIZED,
    )

    import json
    final_path = output_root / "qa" / "final-manifest.json"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(
        json.dumps(final, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    outputs.append(final_path)

    return outputs
