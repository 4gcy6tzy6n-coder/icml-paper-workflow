import shutil
from pathlib import Path

from paperflow.config import WorkflowConfig
from paperflow.errors import InvalidStageError
from paperflow.models.common import WorkflowStage
from paperflow.models.qa import WorkflowManifest
from paperflow.paths import WorkspacePaths
from paperflow.util.hashing import sha256_file
from paperflow.util.jsonio import read_json, write_json

_ALLOWED_TRANSITIONS: dict[WorkflowStage, WorkflowStage] = {
    WorkflowStage.INITIALIZED: WorkflowStage.PARSED,
    WorkflowStage.PARSED: WorkflowStage.IR_READY,
    WorkflowStage.IR_READY: WorkflowStage.REPORT_READY,
    WorkflowStage.REPORT_READY: WorkflowStage.STORYBOARD_READY,
    WorkflowStage.STORYBOARD_READY: WorkflowStage.RENDERED,
    WorkflowStage.RENDERED: WorkflowStage.CONTENT_QA_PASSED,
    WorkflowStage.CONTENT_QA_PASSED: WorkflowStage.VISUAL_QA_PASSED,
    WorkflowStage.VISUAL_QA_PASSED: WorkflowStage.FINALIZED,
}


def create_manifest(
    pdf_path: Path, workspace: Path, config_path: Path | None = None
) -> WorkflowManifest:
    pdf_path = pdf_path.resolve()
    workspace = workspace.resolve()

    config = WorkflowConfig()
    if config_path is not None:
        import yaml

        with open(config_path) as f:
            config = WorkflowConfig(**yaml.safe_load(f))

    pdf_sha256 = sha256_file(pdf_path)

    ws_paths = WorkspacePaths(workspace)
    ws_paths.create_directories()

    input_pdf = ws_paths.source_dir / "input.pdf"
    shutil.copy2(pdf_path, input_pdf)

    manifest = WorkflowManifest(
        stage=WorkflowStage.INITIALIZED,
        source_pdf=str(pdf_path),
        source_sha256=pdf_sha256,
        workspace=str(workspace),
        config=config,
    )
    save_manifest(workspace, manifest)
    return manifest


def load_manifest(workspace: Path) -> WorkflowManifest:
    ws_paths = WorkspacePaths(workspace)
    data = read_json(ws_paths.manifest)
    return WorkflowManifest.model_validate(data)


def save_manifest(workspace: Path, manifest: WorkflowManifest) -> None:
    ws_paths = WorkspacePaths(workspace)
    write_json(ws_paths.manifest, manifest.model_dump(mode="json"))


def advance_stage(
    workspace: Path, expected: WorkflowStage, target: WorkflowStage
) -> WorkflowManifest:
    manifest = load_manifest(workspace)

    if manifest.stage != expected:
        raise InvalidStageError(
            f"Expected current stage '{expected.value}' but manifest is at "
            f"'{manifest.stage.value}'"
        )

    allowed = _ALLOWED_TRANSITIONS.get(expected)
    if allowed != target:
        raise InvalidStageError(
            f"Transition from '{expected.value}' to '{target.value}' is not allowed. "
            f"Allowed next stage: {allowed.value if allowed else 'none'}"
        )

    manifest = manifest.model_copy(update={"stage": target})
    save_manifest(workspace, manifest)
    return manifest
