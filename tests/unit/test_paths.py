from pathlib import Path

from paperflow.paths import WorkspacePaths


def test_workspace_paths_are_deterministic(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    assert paths.source_dir == tmp_path / "source"
    assert paths.paper_ir == tmp_path / "source" / "paper-ir.json"
    assert paths.storyboard == tmp_path / "slides" / "storyboard.json"
    assert paths.final_manifest == tmp_path / "qa" / "final-manifest.json"
