import json
from pathlib import Path
from typing import Any

import typer

from paperflow import __version__
from paperflow.errors import InvalidStageError
from paperflow.ingest.parser_chain import parse_with_fallback, select_parser_chain
from paperflow.manifest import advance_stage, create_manifest, load_manifest, save_manifest
from paperflow.models.common import WorkflowStage

app = typer.Typer(no_args_is_help=True)


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
        "Next semantic step: read source/parsed-paper.md and write "
        "source/paper-ir.json according to the installed Skill."
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

    if manifest.stage not in (WorkflowStage.PARSED, WorkflowStage.IR_READY):
        raise InvalidStageError(
            f"Expected stage 'parsed' but workspace is at '{manifest.stage.value}'. "
            f"Run `paperflow parse` first."
        )

    ws_paths = WorkspacePaths(ws)
    doc_data = read_json(ws_paths.parsed_document)
    document = ParsedDocument.model_validate(doc_data)

    evidence = build_evidence_map(document)
    write_json(ws_paths.evidence_map, [ev.model_dump(mode="json") for ev in evidence])

    packet = build_semantic_packet(document, evidence, ws_paths.paper_ir)
    packet_path = ws_paths.source_dir / "semantic-packet.md"
    packet_path.write_text(packet, encoding="utf-8")

    typer.echo(f"Evidence map built: {len(evidence)} references")
    typer.echo(f"Semantic packet: {packet_path}")
    typer.echo("Next: Author source/paper-ir.json, then run `paperflow validate-ir`.")


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

    if manifest.stage not in (WorkflowStage.PARSED, WorkflowStage.IR_READY):
        raise InvalidStageError(
            f"Expected stage 'parsed' but workspace is at '{manifest.stage.value}'."
        )

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

    advance_stage(ws, manifest.stage, WorkflowStage.IR_READY)

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

    ws_paths = WorkspacePaths(ws)
    if not ws_paths.report_qmd.exists():
        typer.echo(f"Error: {ws_paths.report_qmd} not found.", err=True)
        raise typer.Exit(code=4)

    ir_data = read_json(ws_paths.paper_ir)
    ir = PaperIR.model_validate(ir_data)
    evidence = ir.evidence

    issues = validate_report_qmd(ws_paths.report_qmd, evidence)
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

    if manifest.stage != WorkflowStage.REPORT_READY:
        raise InvalidStageError(
            f"Expected stage 'report_ready' but workspace is at '{manifest.stage.value}'. "
            f"Run `paperflow validate-report` first."
        )

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

    ws_paths = WorkspacePaths(ws)

    if not ws_paths.storyboard.exists():
        typer.echo(f"Error: {ws_paths.storyboard} not found.", err=True)
        raise typer.Exit(code=4)

    sb_data = read_json(ws_paths.storyboard)
    storyboard = Storyboard.model_validate(sb_data)

    issues = validate_storyboard(storyboard)
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

    ws_paths = WorkspacePaths(ws)

    result = run_command(
        ["pnpm", "paperflow:render-slides", "--", str(ws)],
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
