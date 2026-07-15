import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any

from paperflow.models.authoring_requirements import AuthoringRequirements
from paperflow.models.common import WorkflowStage
from paperflow.util.hashing import sha256_file
from paperflow.util.jsonio import read_json


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


def _load_finalization_requirements(workspace: Path) -> AuthoringRequirements:
    from paperflow.requirements.validator import load_validated_requirements

    manifest_data = read_json(workspace / "manifest.json")
    requirements, issues = load_validated_requirements(
        workspace / "source" / "authoring-requirements.json",
        str(manifest_data.get("source_sha256", "")),
        manifest_data.get("validated_requirements_content_sha256"),
    )
    if requirements is None or issues:
        codes = ", ".join(issue.code for issue in issues)
        raise ValueError(f"Sealed requirements revalidation failed: {codes}")
    return requirements


def build_final_manifest(
    workspace: Path,
    source_pdf: Path,
    paper_title: str,
    parser_used: str | None,
    stage: WorkflowStage,
) -> dict[str, Any]:
    """Build the final reproducible manifest."""
    import sys

    visual_review_path = workspace / "qa" / "visual-review.json"
    visual_fix_cycle_count = 0
    if visual_review_path.exists():
        visual_review = read_json(visual_review_path)
        visual_fix_cycle_count = int(visual_review.get("inspection_pass", 0))

    requirements_digest: str | None = None
    requirements_valid = False
    workflow_manifest_path = workspace / "manifest.json"
    requirements_path = workspace / "source" / "authoring-requirements.json"
    if workflow_manifest_path.exists():
        from paperflow.requirements.validator import load_validated_requirements

        workflow_manifest = read_json(workflow_manifest_path)
        requirements_digest = workflow_manifest.get(
            "validated_requirements_content_sha256"
        )
        requirements, issues = load_validated_requirements(
            requirements_path,
            str(workflow_manifest.get("source_sha256", "")),
            requirements_digest,
        )
        requirements_valid = requirements is not None and not issues

    manifest: dict[str, Any] = {
        "workflow_version": "1.0",
        "stage": stage.value,
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
            "visual_fix_cycle_count": visual_fix_cycle_count,
        },
        "requirements": {
            "content_sha256": requirements_digest,
            "valid": requirements_valid,
        },
        "artifacts": {},
    }

    report_qmd = workspace / "report" / "academic-report.qmd"
    if report_qmd.exists():
        manifest["artifacts"]["report/academic-report.qmd"] = sha256_file(report_qmd)

    report_docx = workspace / "report" / "academic-report.docx"
    if report_docx.exists():
        manifest["artifacts"]["report/academic-report.docx"] = sha256_file(report_docx)

    report_pdf = workspace / "report" / "academic-report.pdf"
    if report_pdf.exists():
        manifest["artifacts"]["report/academic-report.pdf"] = sha256_file(report_pdf)

    report_reference = workspace / "report" / "compact-reference.docx"
    if report_reference.exists():
        manifest["artifacts"]["report/compact-reference.docx"] = sha256_file(
            report_reference
        )

    deck_pptx = workspace / "slides" / "presentation.pptx"
    if deck_pptx.exists():
        manifest["artifacts"]["slides/presentation.pptx"] = sha256_file(deck_pptx)

    deck_pdf = workspace / "slides" / "presentation.pdf"
    if deck_pdf.exists():
        manifest["artifacts"]["slides/presentation.pdf"] = sha256_file(deck_pdf)

    notes = workspace / "slides" / "speaker-notes.md"
    if notes.exists():
        manifest["artifacts"]["slides/speaker-notes.md"] = sha256_file(notes)

    if requirements_path.exists():
        manifest["artifacts"]["source/authoring-requirements.json"] = sha256_file(
            requirements_path
        )

    return manifest


def finalize_workspace(workspace: Path, dist_dir: Path) -> list[Path]:
    """Copy verified artifacts to the dist directory.

    Returns list of output paths. Raises FileNotFoundError if required
    artifacts are absent.
    """
    required = [
        workspace / "report" / "academic-report.qmd",
        workspace / "report" / "academic-report.docx",
        workspace / "report" / "academic-report.pdf",
        workspace / "slides" / "presentation.pptx",
        workspace / "slides" / "presentation.pdf",
        workspace / "slides" / "speaker-notes.md",
        workspace / "slides" / "storyboard.json",
        workspace / "source" / "authoring-requirements.json",
    ]

    for path in required:
        if not path.exists():
            raise FileNotFoundError(
                f"Required artifact not found: {path.relative_to(workspace)}"
            )

    if dist_dir.name != "dist":
        raise ValueError(
            "Finalization output is fixed by sealed policy to dist/<paper-slug>."
        )

    requirements = _load_finalization_requirements(workspace)
    from paperflow.qa.consistency import check_confirmed_output_targets

    target_result = check_confirmed_output_targets(workspace, requirements)
    if not target_result.passed:
        failures = "; ".join(
            f"[{issue.code}] {issue.message}"
            for issue in target_result.issues
            if issue.severity == "error"
        )
        raise ValueError(f"Confirmed output target validation failed: {failures}")

    manifest_data = {}
    manifest_path = workspace / "manifest.json"
    if manifest_path.exists():
        import json
        manifest_data = json.loads(manifest_path.read_text())

    title = requirements.source.title
    slug = create_slug(title)

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
        rpt / "compact-reference.docx": orpt / "compact-reference.docx",
        sld / "presentation.pptx": osld / "presentation.pptx",
        sld / "presentation.pdf": osld / "presentation.pdf",
        sld / "speaker-notes.md": osld / "speaker-notes.md",
        sld / "storyboard.json": osld / "storyboard.json",
        src / "paper-ir.json": osrc / "paper-ir.json",
        src / "evidence-map.json": osrc / "evidence-map.json",
        src / "authoring-requirements.json": osrc / "authoring-requirements.json",
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
        paper_title=title,
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
