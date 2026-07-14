import json
from pathlib import Path

import typer

from paperflow import __version__
from paperflow.manifest import create_manifest, load_manifest

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
