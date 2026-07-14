import json

from typer.testing import CliRunner

from paperflow.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "paperflow 0.1.0"


def test_init_command(tmp_path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    result = runner.invoke(app, ["init", str(pdf), str(ws)])
    assert result.exit_code == 0
    assert "Initialized:" in result.stdout
    assert "Stage: initialized" in result.stdout


def test_status_command(tmp_path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    runner.invoke(app, ["init", str(pdf), str(ws)])

    result = runner.invoke(app, ["status", str(ws)])
    assert result.exit_code == 0
    assert "Stage: initialized" in result.stdout


def test_status_command_json(tmp_path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy content\n")
    ws = tmp_path / ".work" / "test-paper"

    runner.invoke(app, ["init", str(pdf), str(ws)])

    result = runner.invoke(app, ["status", str(ws), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["stage"] == "initialized"
    assert len(data["source_sha256"]) == 64
