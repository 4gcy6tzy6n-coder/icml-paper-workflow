import typer

from paperflow import __version__

app = typer.Typer(no_args_is_help=True)


@app.callback(invoke_without_command=True)
def _callback() -> None:
    """PaperFlow: Convert research papers into reports and editable slide decks."""
    pass


@app.command()
def version() -> None:
    """Print the installed PaperFlow version."""
    typer.echo(f"paperflow {__version__}")
