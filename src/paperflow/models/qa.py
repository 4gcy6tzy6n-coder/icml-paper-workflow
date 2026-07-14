from typing import Literal

from pydantic import BaseModel, Field

from paperflow.config import WorkflowConfig
from paperflow.models.common import Severity, WorkflowStage


class ValidationIssue(BaseModel):
    code: str
    severity: Severity
    message: str
    location: str | None = None


class QAResult(BaseModel):
    passed: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    metrics: dict[str, float | int | str] = Field(default_factory=dict)


class RenderResult(BaseModel):
    success: bool
    output_paths: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class WorkflowManifest(BaseModel):
    workflow_version: Literal["1.0"] = "1.0"
    stage: WorkflowStage
    source_pdf: str
    source_sha256: str
    workspace: str
    config: WorkflowConfig = Field(default_factory=WorkflowConfig)
    parser_used: str | None = None
    fallbacks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    completed_steps: list[str] = Field(default_factory=list)
