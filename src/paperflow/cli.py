import json
from pathlib import Path

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
