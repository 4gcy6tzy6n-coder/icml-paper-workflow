import json
from pathlib import Path
from typing import Any

import typer

from paperflow import __version__
from paperflow.errors import InvalidStageError
from paperflow.ingest.parser_chain import parse_with_fallback, select_parser_chain
from paperflow.manifest import advance_stage, create_manifest, load_manifest, save_manifest
from paperflow.models.authoring_requirements import AuthoringRequirements
from paperflow.models.common import WorkflowStage

app = typer.Typer(no_args_is_help=True)


def _load_validated_requirements_or_exit(
    workspace: Path,
) -> AuthoringRequirements:
    from paperflow.paths import WorkspacePaths
    from paperflow.requirements.validator import load_validated_requirements
    from paperflow.util.jsonio import write_json

    manifest = load_manifest(workspace)
    paths = WorkspacePaths(workspace)
    requirements, issues = load_validated_requirements(
        paths.authoring_requirements,
        manifest.source_sha256,
        manifest.validated_requirements_content_sha256,
    )
    errors = [issue for issue in issues if issue.severity == "error"]
    write_json(
        paths.qa_dir / "requirements-revalidation.json",
        {
            "passed": not errors,
            "issues": [issue.model_dump(mode="json") for issue in issues],
            "validated_content_sha256": manifest.validated_requirements_content_sha256,
        },
    )
    if errors or requirements is None:
        typer.echo(f"Requirements revalidation failed: {len(errors)} error(s)")
        for error in errors:
            typer.echo(f"  [{error.code}] {error.message}")
        raise typer.Exit(code=4)
    return requirements


@app.callback(invoke_without_command=True)
def _callback() -> None:
    """PaperFlow: Convert research papers into reports and editable slide decks."""
    pass


@app.command()
def version() -> None:
    """Print the installed PaperFlow version."""
    typer.echo(f"paperflow {__version__}")


@app.command()
def init(
    pdf: str = typer.Argument(..., help="Path to the source paper PDF"),
    output: str = typer.Argument(..., help="Workspace output directory"),
) -> None:
    """Initialize a new PaperFlow workspace from a PDF."""
    pdf_path = Path(pdf).resolve()
    workspace = Path(output).resolve()

    manifest = create_manifest(pdf_path, workspace)

    typer.echo(f"Initialized: {workspace}")
    typer.echo(f"Stage: {manifest.stage.value}")
    typer.echo(f"Next: paperflow parse {workspace}")


@app.command()
def status(
    workspace: str = typer.Argument(..., help="Workspace directory"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show the current workflow stage of a workspace."""
    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "stage": manifest.stage.value,
                    "source_pdf": manifest.source_pdf,
                    "source_sha256": manifest.source_sha256,
                    "parser_used": manifest.parser_used,
                    "warnings": manifest.warnings,
                },
                indent=2,
            )
        )
    else:
        typer.echo(f"Workspace: {ws}")
        typer.echo(f"Stage: {manifest.stage.value}")
        typer.echo(f"Source PDF: {manifest.source_pdf}")


@app.command()
def parse(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Parse the source PDF into a structured document."""
    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage != WorkflowStage.INITIALIZED:
        raise InvalidStageError(
            f"Expected stage 'initialized' but workspace is at '{manifest.stage.value}'. "
            f"Was `paperflow init` already run?"
        )

    config = manifest.config
    chain = select_parser_chain(config)
    if not chain:
        typer.echo(
            "Error: No parsers are available. Install PyMuPDF (`pip install pymupdf`) "
            "or an optional parser.",
            err=True,
        )
        raise typer.Exit(code=3)

    source_pdf = Path(manifest.source_pdf)
    doc, fallbacks, parser_used = parse_with_fallback(source_pdf, ws, chain)

    from paperflow.ingest.asset_extractor import AssetExtractor
    from paperflow.paths import WorkspacePaths
    from paperflow.util.jsonio import write_json

    try:
        assets = AssetExtractor(source_pdf, ws).extract(doc)
        doc = doc.model_copy(update={"assets": assets})
    except Exception as exc:
        doc = doc.model_copy(
            update={
                "warnings": [
                    *doc.warnings,
                    f"Asset extraction failed; continue without asset registry: {exc}",
                ]
            }
        )

    write_json(WorkspacePaths(ws).parsed_document, doc.model_dump(mode="json"))

    manifest = load_manifest(ws)
    manifest = manifest.model_copy(
        update={
            "parser_used": parser_used,
            "fallbacks": fallbacks,
            "warnings": list(manifest.warnings) + doc.warnings,
        }
    )
    save_manifest(ws, manifest)
    advance_stage(ws, WorkflowStage.INITIALIZED, WorkflowStage.PARSED)

    typer.echo(f"Parser used: {parser_used}")
    if doc.warnings:
        typer.echo(f"Warnings: {len(doc.warnings)}")
        for w in doc.warnings:
            typer.echo(f"  - {w}")
    if fallbacks:
        typer.echo(f"Fallbacks attempted: {', '.join(fallbacks)}")
    typer.echo(
        "Next: run paperflow build-evidence, complete the Skill requirements "
        "interview, and run paperflow validate-requirements."
    )


@app.command()
def build_evidence(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Build the evidence map and semantic authoring packet from a parsed document."""
    from paperflow.evidence.builder import build_evidence_map
    from paperflow.evidence.locator import build_semantic_packet
    from paperflow.models.document import ParsedDocument
    from paperflow.paths import WorkspacePaths
    from paperflow.util.jsonio import read_json, write_json

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage != WorkflowStage.PARSED:
        raise InvalidStageError(
            f"Expected a parsed workspace but workspace is at '{manifest.stage.value}'."
        )

    ws_paths = WorkspacePaths(ws)
    doc_data = read_json(ws_paths.parsed_document)
    document = ParsedDocument.model_validate(doc_data)

    evidence = build_evidence_map(document)
    write_json(ws_paths.evidence_map, [ev.model_dump(mode="json") for ev in evidence])

    packet = build_semantic_packet(document, evidence, ws_paths.paper_ir)
    packet_path = ws_paths.semantic_packet
    packet_path.write_text(packet, encoding="utf-8")

    typer.echo(f"Evidence map built: {len(evidence)} references")
    typer.echo(f"Semantic packet: {packet_path}")
    typer.echo(
        "Next: complete the Skill requirements interview, write "
        "source/authoring-requirements.json, and run paperflow validate-requirements."
    )


@app.command()
def validate_requirements(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Validate confirmed authoring requirements for this source PDF."""
    from paperflow.paths import WorkspacePaths
    from paperflow.requirements.validator import (
        validate_evidence_outputs,
        validate_requirements_file,
    )
    from paperflow.util.jsonio import write_json

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)
    if manifest.stage not in (WorkflowStage.PARSED, WorkflowStage.REQUIREMENTS_READY):
        raise InvalidStageError(
            "Expected stage 'parsed' or 'requirements_ready' but workspace is at "
            f"'{manifest.stage.value}'."
        )

    paths = WorkspacePaths(ws)
    requirements, issues = validate_requirements_file(
        paths.authoring_requirements,
        manifest.source_sha256,
    )
    issues.extend(validate_evidence_outputs(paths.evidence_map, paths.semantic_packet))
    errors = [issue for issue in issues if issue.severity == "error"]
    write_json(
        paths.qa_dir / "requirements-validation.json",
        {
            "passed": not errors,
            "issues": [issue.model_dump(mode="json") for issue in issues],
        },
    )
    if errors or requirements is None:
        typer.echo(f"Requirements invalid: {len(errors)} error(s)")
        for error in errors:
            typer.echo(f"  [{error.code}] {error.message}")
        raise typer.Exit(code=4)

    manifest = manifest.model_copy(
        update={
            "validated_requirements_content_sha256": (
                requirements.confirmation.content_sha256
            )
        }
    )
    save_manifest(ws, manifest)
    if manifest.stage == WorkflowStage.PARSED:
        advance_stage(ws, WorkflowStage.PARSED, WorkflowStage.REQUIREMENTS_READY)
    typer.echo("Requirements validation: PASS")
    typer.echo("Stage: requirements_ready")
    typer.echo("Next: author source/paper-ir.json and run paperflow validate-ir.")


@app.command()
def validate_ir(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Validate a Paper IR file against evidence coverage gates."""
    from paperflow.evidence.validator import validate_paper_ir
    from paperflow.models.paper_ir import PaperIR
    from paperflow.paths import WorkspacePaths
    from paperflow.util.jsonio import read_json

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage not in (
        WorkflowStage.REQUIREMENTS_READY,
        WorkflowStage.IR_READY,
    ):
        raise InvalidStageError(
            "Expected stage 'requirements_ready' but workspace is at "
            f"'{manifest.stage.value}'. Run paperflow validate-requirements first."
        )

    _load_validated_requirements_or_exit(ws)

    ws_paths = WorkspacePaths(ws)

    if not ws_paths.paper_ir.exists():
        typer.echo(f"Error: {ws_paths.paper_ir} not found.", err=True)
        raise typer.Exit(code=4)

    ir_data = read_json(ws_paths.paper_ir)
    ir = PaperIR.model_validate(ir_data)

    issues = validate_paper_ir(ir, ir.evidence)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    qa_dir = ws / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    qa_path = qa_dir / "ir-validation.json"

    from paperflow.util.jsonio import write_json
    write_json(
        qa_path,
        {
            "passed": len(errors) == 0,
            "issues": [i.model_dump(mode="json") for i in issues],
            "evidence_coverage": _compute_coverage(ir),
        },
    )

    if errors:
        typer.echo(f"Paper IR invalid: {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            typer.echo(f"  [{e.code}] {e.message}")
        for w in warnings:
            typer.echo(f"  [{w.code}] (warning) {w.message}")
        raise typer.Exit(code=4)

    if manifest.stage == WorkflowStage.REQUIREMENTS_READY:
        advance_stage(
            ws,
            WorkflowStage.REQUIREMENTS_READY,
            WorkflowStage.IR_READY,
        )

    coverage = _compute_coverage(ir)
    typer.echo("Paper IR valid.")
    typer.echo(f"Evidence coverage: {coverage:.0%}")
    typer.echo("Stage: ir_ready")
    typer.echo("Next: author report/report-outline.json and report/academic-report.qmd.")


def _compute_coverage(ir: Any) -> float:
    total_claims = (
        len(ir.contributions)
        + len(ir.findings)
        + len(ir.numeric_results)
        + len(ir.limitations)
        + 1  # research problem
        + 1  # experimental setup
    )
    if total_claims == 0:
        return 0.0
    ev_ids = {ev.id for ev in ir.evidence}
    covered = 0
    for section in [
        ir.contributions,
        ir.findings,
        ir.numeric_results,
        ir.limitations,
    ]:
        for claim in section:
            if any(eid in ev_ids for eid in claim.evidence_ids):
                covered += 1
    covered += 1  # research problem
    covered += 1  # experimental setup
    return min(1.0, covered / total_claims)


@app.command()
def scaffold_report(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Scaffold a report outline and QMD template from a validated Paper IR."""
    from paperflow.models.paper_ir import PaperIR
    from paperflow.paths import WorkspacePaths
    from paperflow.report.scaffold import scaffold_outline, scaffold_qmd
    from paperflow.util.jsonio import read_json, write_json

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage != WorkflowStage.IR_READY:
        raise InvalidStageError(
            f"Expected stage 'ir_ready' but workspace is at '{manifest.stage.value}'. "
            f"Run `paperflow validate-ir` first."
        )

    _load_validated_requirements_or_exit(ws)

    ws_paths = WorkspacePaths(ws)
    ir_data = read_json(ws_paths.paper_ir)
    ir = PaperIR.model_validate(ir_data)

    outline = scaffold_outline(ir.metadata.title)
    outline_path = ws_paths.report_dir / "report-outline.json"
    write_json(outline_path, outline.model_dump(mode="json"))

    scaffold_qmd(outline, ws_paths.report_qmd)

    typer.echo(f"Outline: {outline_path}")
    typer.echo(f"QMD scaffold: {ws_paths.report_qmd}")
    typer.echo(f"Next: fill in full prose in {ws_paths.report_qmd}, ")
    typer.echo("then run `paperflow validate-report`.")


@app.command()
def validate_report(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Validate a completed report QMD against evidence and style rules."""
    from paperflow.models.paper_ir import PaperIR
    from paperflow.paths import WorkspacePaths
    from paperflow.report.validator import validate_report_qmd
    from paperflow.util.jsonio import read_json, write_json

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage != WorkflowStage.IR_READY:
        raise InvalidStageError(
            f"Expected stage 'ir_ready' but workspace is at '{manifest.stage.value}'. "
            f"Complete report authoring first."
        )

    requirements = _load_validated_requirements_or_exit(ws)

    ws_paths = WorkspacePaths(ws)
    if not ws_paths.report_qmd.exists():
        typer.echo(f"Error: {ws_paths.report_qmd} not found.", err=True)
        raise typer.Exit(code=4)

    ir_data = read_json(ws_paths.paper_ir)
    ir = PaperIR.model_validate(ir_data)
    evidence = ir.evidence

    issues = validate_report_qmd(
        ws_paths.report_qmd,
        evidence,
        requirements.report.target_chinese_characters,
    )
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    qa_path = ws_paths.qa_dir / "report-validation.json"
    ws_paths.qa_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        qa_path,
        {
            "passed": len(errors) == 0,
            "issues": [i.model_dump(mode="json") for i in issues],
        },
    )

    if errors:
        typer.echo(f"Report invalid: {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            typer.echo(f"  [{e.code}] {e.message}")
        raise typer.Exit(code=4)

    advance_stage(ws, WorkflowStage.IR_READY, WorkflowStage.REPORT_READY)

    typer.echo("Report validation: PASS")
    typer.echo("Stage: report_ready")
    typer.echo("Next: author slides/storyboard.json and run `paperflow validate-storyboard`.")


@app.command()
def render_report(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Render the validated report QMD to DOCX and PDF."""
    from paperflow.report.renderer import render_report as render_report_impl

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage not in (
        WorkflowStage.REPORT_READY,
        WorkflowStage.STORYBOARD_READY,
        WorkflowStage.RENDERED,
    ):
        raise InvalidStageError(
            "Expected stage 'report_ready', 'storyboard_ready', or 'rendered' but "
            f"workspace is at '{manifest.stage.value}'. Run `paperflow validate-report` "
            "first."
        )

    _load_validated_requirements_or_exit(ws)

    result = render_report_impl(ws)

    if not result.success:
        typer.echo("Report rendering failed:", err=True)
        for w in result.warnings:
            typer.echo(f"  {w}", err=True)
        raise typer.Exit(code=3)

    for p in result.output_paths:
        typer.echo(f"  {p}")

    if result.warnings:
        for w in result.warnings:
            typer.echo(f"Warning: {w}")

    typer.echo("Report rendered successfully.")


@app.command()
def validate_storyboard(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Validate a slide storyboard against semantic rules."""
    from paperflow.models.slides import Storyboard
    from paperflow.paths import WorkspacePaths
    from paperflow.qa.content import validate_storyboard
    from paperflow.util.jsonio import read_json, write_json

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage != WorkflowStage.REPORT_READY:
        raise InvalidStageError(
            f"Expected stage 'report_ready' but workspace is at '{manifest.stage.value}'. "
            f"Author the storyboard first."
        )

    requirements = _load_validated_requirements_or_exit(ws)

    ws_paths = WorkspacePaths(ws)

    if not ws_paths.storyboard.exists():
        typer.echo(f"Error: {ws_paths.storyboard} not found.", err=True)
        raise typer.Exit(code=4)

    sb_data = read_json(ws_paths.storyboard)
    storyboard = Storyboard.model_validate(sb_data)

    issues = validate_storyboard(storyboard, requirements.presentation.target_slides)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    ws_paths.qa_dir.mkdir(parents=True, exist_ok=True)
    qa_path = ws_paths.qa_dir / "storyboard-validation.json"
    write_json(
        qa_path,
        {
            "passed": len(errors) == 0,
            "issues": [i.model_dump(mode="json") for i in issues],
        },
    )

    if errors:
        typer.echo(f"Storyboard invalid: {len(errors)} error(s)")
        for e in errors:
            typer.echo(f"  [{e.code}] {e.message}")
        raise typer.Exit(code=4)

    for w in warnings:
        typer.echo(f"Warning: [{w.code}] {w.message}")

    advance_stage(ws, WorkflowStage.REPORT_READY, WorkflowStage.STORYBOARD_READY)

    typer.echo("Storyboard validation: PASS")
    typer.echo("Stage: storyboard_ready")
    typer.echo("Next: run `paperflow render-slides`.")


@app.command()
def render_slides(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Render the slides storyboard to PPTX and speaker notes."""
    from paperflow.paths import WorkspacePaths
    from paperflow.util.commands import run_command

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage != WorkflowStage.STORYBOARD_READY:
        raise InvalidStageError(
            f"Expected stage 'storyboard_ready' but workspace is at "
            f"'{manifest.stage.value}'. Run `paperflow validate-storyboard` first."
        )

    _load_validated_requirements_or_exit(ws)

    ws_paths = WorkspacePaths(ws)

    result = run_command(
        ["pnpm", "paperflow:render-slides", str(ws)],
        timeout_s=120,
    )

    if result.returncode != 0:
        typer.echo("Slide rendering failed:", err=True)
        typer.echo(result.stderr, err=True)
        raise typer.Exit(code=3)

    if not ws_paths.deck_pptx.exists():
        typer.echo(f"Error: {ws_paths.deck_pptx} was not created.", err=True)
        raise typer.Exit(code=3)

    if not ws_paths.notes_markdown.exists():
        typer.echo(f"Error: {ws_paths.notes_markdown} was not created.", err=True)
        raise typer.Exit(code=3)

    advance_stage(ws, WorkflowStage.STORYBOARD_READY, WorkflowStage.RENDERED)

    typer.echo(f"PPTX: {ws_paths.deck_pptx}")
    typer.echo(f"Notes: {ws_paths.notes_markdown}")
    typer.echo("Stage: rendered")
    typer.echo("Next: run `paperflow qa-content`.")


@app.command()
def qa_content(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Run cross-artifact content QA checks."""
    from paperflow.qa.consistency import check_cross_artifact_consistency

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage != WorkflowStage.RENDERED:
        raise InvalidStageError(
            f"Expected stage 'rendered' but workspace is at "
            f"'{manifest.stage.value}'. Run `paperflow render-slides` first."
        )

    requirements = _load_validated_requirements_or_exit(ws)

    result = check_cross_artifact_consistency(ws, requirements)
    qa_dir = ws / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)

    from paperflow.util.jsonio import write_json
    write_json(
        qa_dir / "content-qa.json",
        {
            "passed": result.passed,
            "issues": [i.model_dump(mode="json") for i in result.issues],
            "metrics": result.metrics,
        },
    )

    if not result.passed:
        typer.echo("Content QA: FAIL")
        for i in result.issues:
            if i.severity == "error":
                typer.echo(f"  [{i.code}] {i.message}")
        raise typer.Exit(code=4)

    advance_stage(ws, WorkflowStage.RENDERED, WorkflowStage.CONTENT_QA_PASSED)

    ev_cov = result.metrics.get("evidence_coverage", 0)
    typer.echo("Content QA: PASS")
    typer.echo(f"Evidence references: {ev_cov:.0%}")
    typer.echo("Placeholder scan: PASS")
    typer.echo("Stage: content_qa_passed")
    typer.echo("Next: run `paperflow render-preview` for visual QA.")


@app.command()
def render_preview(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Render slide preview images and contact sheet for visual inspection."""
    from paperflow.paths import WorkspacePaths
    from paperflow.qa.preview import (
        convert_pptx_to_pdf,
        create_contact_sheet,
        rasterize_pdf_to_images,
    )

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage not in (WorkflowStage.RENDERED, WorkflowStage.CONTENT_QA_PASSED):
        raise InvalidStageError(
            f"Expected stage 'rendered' or 'content_qa_passed' but workspace is at "
            f"'{manifest.stage.value}'."
        )

    _load_validated_requirements_or_exit(ws)

    ws_paths = WorkspacePaths(ws)
    if not ws_paths.deck_pptx.exists():
        typer.echo(f"Error: {ws_paths.deck_pptx} not found.", err=True)
        raise typer.Exit(code=4)

    pdf_result = convert_pptx_to_pdf(ws_paths.deck_pptx)
    if not pdf_result.success:
        for w in pdf_result.warnings:
            typer.echo(f"Error: {w}", err=True)
        raise typer.Exit(code=3)

    slide_img_dir = ws_paths.qa_dir / "slide-images"
    img_result = rasterize_pdf_to_images(ws_paths.deck_pdf, slide_img_dir)
    if not img_result.success:
        for w in img_result.warnings:
            typer.echo(f"Error: {w}", err=True)
        raise typer.Exit(code=3)

    contact_sheet = create_contact_sheet(
        slide_img_dir, ws_paths.qa_dir / "contact-sheet.png"
    )

    typer.echo(f"Preview images: {slide_img_dir}")
    typer.echo(f"  {len(img_result.output_paths)} slides")
    if contact_sheet.success:
        typer.echo(f"Contact sheet: {contact_sheet.output_paths[0]}")
    typer.echo("Next: inspect slide images and write qa/visual-review.json.")


@app.command()
def validate_visual_review(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Validate the visual review JSON against mandatory rules."""
    from paperflow.models.slides import Storyboard
    from paperflow.paths import WorkspacePaths
    from paperflow.qa.preview import validate_visual_review as validate_vr
    from paperflow.util.jsonio import read_json, write_json

    ws = Path(workspace).resolve()
    manifest = load_manifest(ws)

    if manifest.stage != WorkflowStage.CONTENT_QA_PASSED:
        raise InvalidStageError(
            f"Expected stage 'content_qa_passed' but workspace is at "
            f"'{manifest.stage.value}'. Run `paperflow qa-content` first."
        )

    _load_validated_requirements_or_exit(ws)

    ws_paths = WorkspacePaths(ws)
    review_path = ws_paths.qa_dir / "visual-review.json"

    if not review_path.exists():
        typer.echo(f"Error: {review_path} not found.", err=True)
        raise typer.Exit(code=4)

    review = read_json(review_path)

    sb_data = read_json(ws_paths.storyboard)
    storyboard = Storyboard.model_validate(sb_data)
    total_slides = len(storyboard.slides)

    issues = validate_vr(review, total_slides)
    errors = [i for i in issues if i.severity == "error"]

    write_json(
        ws_paths.qa_dir / "visual-review-validation.json",
        {
            "passed": len(errors) == 0,
            "issues": [i.model_dump(mode="json") for i in issues],
        },
    )

    if errors:
        typer.echo(f"Visual review invalid: {len(errors)} error(s)")
        for e in errors:
            typer.echo(f"  [{e.code}] {e.message}")
        raise typer.Exit(code=4)

    advance_stage(ws, WorkflowStage.CONTENT_QA_PASSED, WorkflowStage.VISUAL_QA_PASSED)

    typer.echo("Visual review: PASS")
    typer.echo(f"Fix cycles: {review.get('inspection_pass', 0)}")
    typer.echo("Stage: visual_qa_passed")
    typer.echo("Next: run `paperflow finalize`.")


@app.command()
def finalize(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Finalize and copy all verified artifacts to the distribution directory."""
    from paperflow.qa.finalize import finalize_workspace

    ws = Path(workspace).resolve()
    dist_dir = Path("dist").resolve()

    manifest = load_manifest(ws)

    if manifest.stage != WorkflowStage.VISUAL_QA_PASSED:
        raise InvalidStageError(
            f"Expected stage 'visual_qa_passed' but workspace is at "
            f"'{manifest.stage.value}'. Run `paperflow validate-visual-review` first."
        )

    _load_validated_requirements_or_exit(ws)

    try:
        outputs = finalize_workspace(ws, dist_dir)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(f"Finalization failed: {e}", err=True)
        raise typer.Exit(code=4) from None

    advance_stage(ws, WorkflowStage.VISUAL_QA_PASSED, WorkflowStage.FINALIZED)

    typer.echo(f"Finalized: {dist_dir}")
    for p in outputs:
        typer.echo(f"  {p.relative_to(dist_dir)}")
    typer.echo("Final manifest: qa/final-manifest.json")


@app.command()
def doctor() -> None:
    """Check the runtime environment for required and optional tools."""
    from paperflow.util.check_environment import check_environment

    checks = check_environment()

    typer.echo(f"{'Tool':<16} {'Required':<10} {'Version':<30} {'Status':<8}")
    typer.echo("-" * 66)

    has_missing_required = False

    for c in checks:
        status = "✓" if c.available else ("✗" if c.required else "(opt) ✗")
        version = c.version or "N/A"
        typer.echo(f"{c.name:<16} {'yes' if c.required else 'no':<10} {version:<30} {status:<8}")
        if c.required and not c.available:
            has_missing_required = True
            if c.action:
                typer.echo(f"  → {c.action}")

    if has_missing_required:
        typer.echo("\nSome required tools are missing. Install them and try again.")
        raise typer.Exit(code=1)
    else:
        typer.echo("\nAll required tools available.")
