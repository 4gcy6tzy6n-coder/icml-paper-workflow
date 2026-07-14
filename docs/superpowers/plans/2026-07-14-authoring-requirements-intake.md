# Authoring Requirements Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Add a mandatory, confirmed, PDF-bound authoring requirements interview gate before PaperFlow can validate a Paper IR or generate the Chinese report and presentation.

**Architecture:** The existing project skill conducts one-question-at-a-time intake and writes one canonical JSON record only after explicit confirmation. Deterministic Pydantic models, a digest helper, a file validator, a new requirements_ready state, and a validate-requirements CLI command enforce the gate before the existing semantic pipeline.

**Tech Stack:** Python 3.11+, Pydantic 2.7+, Typer 0.12+, pytest 8+, Markdown project skills, Ruff, mypy.

## Global Constraints

- Enhance skills/icml-paper-to-report-deck; do not create a standalone skill.
- Parse and build evidence before intake; do not author Paper IR, report prose, or storyboard before requirements validation.
- Ask exactly one question at a time.
- Cover all ten core requirement topics and add adaptive follow-ups where needed.
- Present a complete summary and require explicit user confirmation.
- Persist only source/authoring-requirements.json; do not generate a Markdown requirements copy.
- Bind confirmation to the exact requirements content and exact source PDF SHA-256.
- Do not add an interactive terminal questionnaire.
- Never request or persist credentials, API keys, tokens, passwords, or unrelated personal information.
- Invalid requirements fail with exit code 4 and leave the workflow stage unchanged.
- Keep all existing runtime and rendering dependency requirements unchanged.

## File Structure

- Create src/paperflow/models/authoring_requirements.py for schema and digest logic.
- Create src/paperflow/requirements/validator.py for file, source, and confirmation validation.
- Create tests/fixtures/make_authoring_requirements.py for valid sealed test records.
- Create tests/unit/test_authoring_requirements.py and tests/unit/test_requirements_validator.py.
- Create skills/icml-paper-to-report-deck/references/requirements-intake.md.
- Modify state, manifest, paths, CLI, project skill, workflow contract, public docs, and lifecycle tests.

---

### Task 1: Requirements schema and confirmation digest

**Files:**
- Create: src/paperflow/models/authoring_requirements.py
- Create: tests/fixtures/make_authoring_requirements.py
- Create: tests/unit/test_authoring_requirements.py

**Interfaces:**
- Produces AuthoringRequirements.
- Produces canonical_requirements_content(data) -> dict[str, Any].
- Produces compute_requirements_digest(data) -> str.
- Digest input may be an AuthoringRequirements model or a mapping and excludes confirmation.

- [ ] **Step 1: Write the failing tests**

Create tests/unit/test_authoring_requirements.py:

~~~python
import pytest
from pydantic import ValidationError

from paperflow.models.authoring_requirements import (
    AuthoringRequirements,
    compute_requirements_digest,
)
from tests.fixtures.make_authoring_requirements import make_authoring_requirements


def test_complete_requirements_validate_and_digest_is_stable() -> None:
    data = make_authoring_requirements("a" * 64)
    requirements = AuthoringRequirements.model_validate(data)
    assert compute_requirements_digest(requirements) == data["confirmation"]["content_sha256"]


def test_confirmation_metadata_is_excluded_from_digest() -> None:
    data = make_authoring_requirements("a" * 64)
    digest = compute_requirements_digest(data)
    data["confirmation"]["confirmed_at"] = "2026-07-15T00:00:00Z"
    assert compute_requirements_digest(data) == digest


def test_content_edit_changes_digest() -> None:
    data = make_authoring_requirements("a" * 64)
    digest = data["confirmation"]["content_sha256"]
    data["report"]["purpose"] = "Changed after confirmation"
    assert compute_requirements_digest(data) != digest


def test_blank_required_text_is_rejected() -> None:
    data = make_authoring_requirements("a" * 64)
    data["use_case"]["scenario"] = " "
    with pytest.raises(ValidationError):
        AuthoringRequirements.model_validate(data)


def test_inverted_page_or_slide_range_is_rejected() -> None:
    data = make_authoring_requirements("a" * 64)
    data["presentation"]["target_slides"] = {"minimum": 15, "maximum": 13}
    with pytest.raises(ValidationError):
        AuthoringRequirements.model_validate(data)


def test_enabled_report_requires_formats() -> None:
    data = make_authoring_requirements("a" * 64)
    data["report"]["formats"] = []
    data["deliverables"]["formats"] = ["pptx", "slides_pdf", "speaker_notes"]
    with pytest.raises(ValidationError):
        AuthoringRequirements.model_validate(data)
~~~

- [ ] **Step 2: Run the tests and verify the missing-module failure**

Run:

~~~bash
uv run pytest tests/unit/test_authoring_requirements.py -q
~~~

Expected: collection fails because paperflow.models.authoring_requirements does not exist.

- [ ] **Step 3: Implement the schema and digest**

Create src/paperflow/models/authoring_requirements.py with these complete public types:

~~~python
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256Str = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
ReportFormat = Literal["qmd", "docx", "report_pdf"]
PresentationFormat = Literal["pptx", "slides_pdf", "speaker_notes"]
DeliveryFormat = ReportFormat | PresentationFormat


class PositiveRange(BaseModel):
    minimum: int = Field(ge=1)
    maximum: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self) -> PositiveRange:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class SourceRequirements(BaseModel):
    pdf_sha256: Sha256Str
    title: NonBlankStr


class AudienceRequirements(BaseModel):
    role: NonBlankStr
    background: NonBlankStr
    subject_familiarity: Literal["beginner", "intermediate", "advanced", "mixed"]


class UseCaseRequirements(BaseModel):
    scenario: NonBlankStr
    desired_outcome: NonBlankStr
    audience: AudienceRequirements


class ReportRequirements(BaseModel):
    required: bool
    purpose: NonBlankStr | None = None
    target_pages: PositiveRange | None = None
    target_chinese_characters: PositiveRange | None = None
    formats: list[ReportFormat] = Field(default_factory=list)
    focus_topics: list[NonBlankStr] = Field(default_factory=list)
    de_emphasized_topics: list[NonBlankStr] = Field(default_factory=list)
    technical_depth: Literal["overview", "balanced", "deep"] | None = None
    narrative_preference: NonBlankStr | None = None
    reading_context: NonBlankStr | None = None

    @model_validator(mode="after")
    def complete_when_required(self) -> ReportRequirements:
        values = (
            self.purpose,
            self.target_pages,
            self.target_chinese_characters,
            self.technical_depth,
            self.narrative_preference,
            self.reading_context,
        )
        if self.required and (any(value is None for value in values) or not self.formats):
            raise ValueError("enabled report settings must be complete")
        return self


class PresentationRequirements(BaseModel):
    required: bool
    purpose: NonBlankStr | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    target_slides: PositiveRange | None = None
    formats: list[PresentationFormat] = Field(default_factory=list)
    focus_topics: list[NonBlankStr] = Field(default_factory=list)
    speaker_notes_required: bool | None = None
    speaking_context: NonBlankStr | None = None

    @model_validator(mode="after")
    def complete_when_required(self) -> PresentationRequirements:
        values = (
            self.purpose,
            self.duration_minutes,
            self.target_slides,
            self.speaker_notes_required,
            self.speaking_context,
        )
        if self.required and (any(value is None for value in values) or not self.formats):
            raise ValueError("enabled presentation settings must be complete")
        return self


class LanguageRequirements(BaseModel):
    locale: Literal["zh-CN"]
    preserve_english_terms: bool
    translation_preferences: NonBlankStr


class VisualRequirements(BaseModel):
    style: NonBlankStr
    template_path: NonBlankStr | None = None
    brand_requirements: list[NonBlankStr] = Field(default_factory=list)
    accessibility_requirements: list[NonBlankStr] = Field(default_factory=list)


class EvidencePolicyRequirements(BaseModel):
    allow_web_research: bool
    allow_generated_result_figures: bool
    prefer_original_figures: bool
    citation_expectations: NonBlankStr


class DeliverableRequirements(BaseModel):
    formats: list[DeliveryFormat] = Field(min_length=1)
    output_location: NonBlankStr
    naming_requirements: NonBlankStr


class ConfirmationRequirements(BaseModel):
    status: Literal["confirmed"]
    confirmed_at: datetime
    content_sha256: Sha256Str


class AuthoringRequirements(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    source: SourceRequirements
    use_case: UseCaseRequirements
    report: ReportRequirements
    presentation: PresentationRequirements
    language: LanguageRequirements
    visual: VisualRequirements
    evidence_policy: EvidencePolicyRequirements
    deliverables: DeliverableRequirements
    user_constraints: list[NonBlankStr] = Field(default_factory=list)
    assumptions: list[NonBlankStr] = Field(default_factory=list)
    confirmation: ConfirmationRequirements

    @model_validator(mode="after")
    def formats_match_enabled_outputs(self) -> AuthoringRequirements:
        expected: set[str] = set()
        if self.report.required:
            expected.update(self.report.formats)
        if self.presentation.required:
            expected.update(self.presentation.formats)
        if set(self.deliverables.formats) != expected:
            raise ValueError("deliverable formats must match enabled output formats")
        return self


RequirementsInput = AuthoringRequirements | Mapping[str, Any]


def canonical_requirements_content(data: RequirementsInput) -> dict[str, Any]:
    payload = data.model_dump(mode="json") if isinstance(data, AuthoringRequirements) else dict(data)
    return {key: value for key, value in payload.items() if key != "confirmation"}


def compute_requirements_digest(data: RequirementsInput) -> str:
    canonical = json.dumps(
        canonical_requirements_content(data),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
~~~

Create tests/fixtures/make_authoring_requirements.py:

~~~python
from typing import Any

from paperflow.models.authoring_requirements import compute_requirements_digest


def make_authoring_requirements(pdf_sha256: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": "1.0",
        "source": {"pdf_sha256": pdf_sha256, "title": "Test Paper"},
        "use_case": {
            "scenario": "研究生组会",
            "desired_outcome": "准确理解论文贡献、结果与局限",
            "audience": {
                "role": "研究生",
                "background": "机器学习基础",
                "subject_familiarity": "intermediate",
            },
        },
        "report": {
            "required": True,
            "purpose": "论文精读报告",
            "target_pages": {"minimum": 7, "maximum": 9},
            "target_chinese_characters": {"minimum": 7000, "maximum": 10000},
            "formats": ["qmd", "docx", "report_pdf"],
            "focus_topics": ["方法", "实验", "局限"],
            "de_emphasized_topics": ["逐条复述参考文献"],
            "technical_depth": "deep",
            "narrative_preference": "证据驱动的学术叙事",
            "reading_context": "会前精读与会后复习",
        },
        "presentation": {
            "required": True,
            "purpose": "十五分钟组会汇报",
            "duration_minutes": 15,
            "target_slides": {"minimum": 13, "maximum": 15},
            "formats": ["pptx", "slides_pdf", "speaker_notes"],
            "focus_topics": ["核心结论", "关键实验", "失败分析"],
            "speaker_notes_required": True,
            "speaking_context": "现场口头汇报",
        },
        "language": {
            "locale": "zh-CN",
            "preserve_english_terms": True,
            "translation_preferences": "中文叙述并保留方法、数据集和指标英文名",
        },
        "visual": {
            "style": "清晰、克制、学术化",
            "template_path": None,
            "brand_requirements": [],
            "accessibility_requirements": ["高对比度", "不以颜色作为唯一编码"],
        },
        "evidence_policy": {
            "allow_web_research": False,
            "allow_generated_result_figures": False,
            "prefer_original_figures": True,
            "citation_expectations": "所有实质性结论追溯到论文证据块",
        },
        "deliverables": {
            "formats": [
                "qmd",
                "docx",
                "report_pdf",
                "pptx",
                "slides_pdf",
                "speaker_notes",
            ],
            "output_location": "workspace/dist/test-paper",
            "naming_requirements": "使用稳定的英文文件名",
        },
        "user_constraints": ["不得夸大论文性能"],
        "assumptions": [],
    }
    data["confirmation"] = {
        "status": "confirmed",
        "confirmed_at": "2026-07-14T12:00:00+08:00",
        "content_sha256": compute_requirements_digest(data),
    }
    return data
~~~

- [ ] **Step 4: Run the model tests**

Run:

~~~bash
uv run pytest tests/unit/test_authoring_requirements.py -q
~~~

Expected: all tests pass.

- [ ] **Step 5: Commit**

~~~bash
git add src/paperflow/models/authoring_requirements.py tests/fixtures/make_authoring_requirements.py tests/unit/test_authoring_requirements.py
git commit -m "feat: add authoring requirements schema"
~~~

### Task 2: File validator

**Files:**
- Create: src/paperflow/requirements/__init__.py
- Create: src/paperflow/requirements/validator.py
- Create: tests/unit/test_requirements_validator.py

**Interfaces:**
- Produces validate_requirements_file(path: Path, expected_source_sha256: str) -> tuple[AuthoringRequirements | None, list[ValidationIssue]].
- Returns errors without modifying workspace files or manifest state.

- [ ] **Step 1: Write failing validator tests**

Create tests/unit/test_requirements_validator.py:

~~~python
from pathlib import Path

from paperflow.requirements.validator import validate_requirements_file
from paperflow.util.jsonio import write_json
from tests.fixtures.make_authoring_requirements import make_authoring_requirements


def test_valid_file_returns_model_and_no_issues(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    write_json(path, make_authoring_requirements("a" * 64))
    requirements, issues = validate_requirements_file(path, "a" * 64)
    assert requirements is not None
    assert issues == []


def test_missing_file_returns_req_file_missing(tmp_path: Path) -> None:
    _, issues = validate_requirements_file(tmp_path / "missing.json", "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_FILE_MISSING"}


def test_malformed_json_returns_req_json_invalid(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    path.write_text("{", encoding="utf-8")
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_JSON_INVALID"}


def test_wrong_pdf_returns_req_source_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    write_json(path, make_authoring_requirements("b" * 64))
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_SOURCE_MISMATCH"}


def test_content_edit_returns_digest_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    data = make_authoring_requirements("a" * 64)
    data["visual"]["style"] = "changed"
    write_json(path, data)
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_CONFIRMATION_DIGEST_MISMATCH"}


def test_schema_error_returns_req_schema_invalid(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    data = make_authoring_requirements("a" * 64)
    data["use_case"]["scenario"] = ""
    write_json(path, data)
    _, issues = validate_requirements_file(path, "a" * 64)
    assert {issue.code for issue in issues} == {"REQ_SCHEMA_INVALID"}
~~~

- [ ] **Step 2: Run and verify the missing-package failure**

~~~bash
uv run pytest tests/unit/test_requirements_validator.py -q
~~~

Expected: collection fails because paperflow.requirements.validator is missing.

- [ ] **Step 3: Implement the validator**

Create an empty src/paperflow/requirements/__init__.py. Create validator.py:

~~~python
import json
from pathlib import Path

from pydantic import ValidationError

from paperflow.models.authoring_requirements import (
    AuthoringRequirements,
    compute_requirements_digest,
)
from paperflow.models.common import Severity
from paperflow.models.qa import ValidationIssue
from paperflow.util.jsonio import read_json


def _error(code: str, message: str, location: str) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        severity=Severity.ERROR,
        message=message,
        location=location,
    )


def validate_requirements_file(
    path: Path, expected_source_sha256: str
) -> tuple[AuthoringRequirements | None, list[ValidationIssue]]:
    if not path.exists():
        return None, [_error("REQ_FILE_MISSING", f"Requirements not found: {path}", str(path))]
    try:
        raw = read_json(path)
    except (json.JSONDecodeError, OSError) as exc:
        return None, [_error("REQ_JSON_INVALID", f"Cannot read requirements JSON: {exc}", str(path))]
    try:
        requirements = AuthoringRequirements.model_validate(raw)
    except ValidationError as exc:
        return None, [_error("REQ_SCHEMA_INVALID", f"Invalid requirements schema: {exc}", str(path))]

    issues: list[ValidationIssue] = []
    if requirements.source.pdf_sha256 != expected_source_sha256:
        issues.append(_error("REQ_SOURCE_MISMATCH", "Requirements belong to another PDF.", "source.pdf_sha256"))
    if compute_requirements_digest(requirements) != requirements.confirmation.content_sha256:
        issues.append(
            _error(
                "REQ_CONFIRMATION_DIGEST_MISMATCH",
                "Requirements changed after confirmation.",
                "confirmation.content_sha256",
            )
        )
    return (requirements if not issues else None), issues
~~~

- [ ] **Step 4: Run focused tests**

~~~bash
uv run pytest tests/unit/test_authoring_requirements.py tests/unit/test_requirements_validator.py -q
~~~

Expected: all tests pass.

- [ ] **Step 5: Commit**

~~~bash
git add src/paperflow/requirements tests/unit/test_requirements_validator.py
git commit -m "feat: validate confirmed authoring requirements"
~~~

### Task 3: Workflow state and CLI gate

**Files:**
- Modify: src/paperflow/models/common.py
- Modify: src/paperflow/manifest.py
- Modify: src/paperflow/paths.py
- Modify: src/paperflow/cli.py
- Modify: tests/unit/test_manifest.py
- Modify: tests/unit/test_paths.py
- Modify: tests/unit/test_cli.py

**Interfaces:**
- Adds WorkflowStage.REQUIREMENTS_READY = requirements_ready.
- Adds WorkspacePaths.authoring_requirements.
- Adds paperflow validate-requirements WORKSPACE.
- validate-ir rejects parsed and accepts requirements_ready for first validation.

- [ ] **Step 1: Write failing state, path, and CLI tests**

Add this path assertion:

~~~python
def test_authoring_requirements_path(tmp_path: Path) -> None:
    paths = WorkspacePaths(tmp_path)
    assert paths.authoring_requirements == tmp_path / "source" / "authoring-requirements.json"
~~~

Update test_full_transition_chain with:

~~~python
(WorkflowStage.PARSED, WorkflowStage.REQUIREMENTS_READY),
(WorkflowStage.REQUIREMENTS_READY, WorkflowStage.IR_READY),
~~~

Add these imports to tests/unit/test_cli.py:

~~~python
from paperflow.manifest import load_manifest
from paperflow.models.common import WorkflowStage
from paperflow.util.jsonio import write_json
from tests.fixtures.make_authoring_requirements import make_authoring_requirements
~~~

Add these tests:

~~~python
def _parsed_requirements_workspace(tmp_path: Path) -> Path:
    pdf = tmp_path / "requirements-paper.pdf"
    make_sample_pdf(pdf)
    workspace = tmp_path / ".work" / "requirements-paper"
    assert runner.invoke(app, ["init", str(pdf), str(workspace)]).exit_code == 0
    assert runner.invoke(app, ["parse", str(workspace)]).exit_code == 0
    return workspace


def test_validate_requirements_advances_stage(tmp_path: Path) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    manifest = load_manifest(workspace)
    write_json(
        workspace / "source" / "authoring-requirements.json",
        make_authoring_requirements(manifest.source_sha256),
    )
    result = runner.invoke(app, ["validate-requirements", str(workspace)])
    assert result.exit_code == 0
    assert "Requirements validation: PASS" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.REQUIREMENTS_READY
    qa = read_json(workspace / "qa" / "requirements-validation.json")
    assert qa["passed"] is True


def test_validate_requirements_missing_file_keeps_parsed_stage(
    tmp_path: Path,
) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    result = runner.invoke(app, ["validate-requirements", str(workspace)])
    assert result.exit_code == 4
    assert "REQ_FILE_MISSING" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.PARSED
    qa = read_json(workspace / "qa" / "requirements-validation.json")
    assert qa["passed"] is False


def test_validate_requirements_digest_mismatch_keeps_parsed_stage(
    tmp_path: Path,
) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    manifest = load_manifest(workspace)
    data = make_authoring_requirements(manifest.source_sha256)
    data["visual"]["style"] = "changed after confirmation"
    write_json(workspace / "source" / "authoring-requirements.json", data)
    result = runner.invoke(app, ["validate-requirements", str(workspace)])
    assert result.exit_code == 4
    assert "REQ_CONFIRMATION_DIGEST_MISMATCH" in result.stdout
    assert load_manifest(workspace).stage == WorkflowStage.PARSED


def test_validate_ir_rejects_parsed_stage(tmp_path: Path) -> None:
    workspace = _parsed_requirements_workspace(tmp_path)
    result = runner.invoke(app, ["validate-ir", str(workspace)])
    assert result.exit_code == 1
    assert result.exception is not None
    assert "requirements_ready" in str(result.exception)
    assert load_manifest(workspace).stage == WorkflowStage.PARSED
~~~

- [ ] **Step 2: Run focused tests and observe missing symbols**

~~~bash
uv run pytest tests/unit/test_paths.py tests/unit/test_manifest.py tests/unit/test_cli.py -q
~~~

Expected: failures for the missing state, path, and command.

- [ ] **Step 3: Implement state, path, and command**

Add REQUIREMENTS_READY between PARSED and IR_READY. Replace the first transitions with:

~~~python
WorkflowStage.INITIALIZED: WorkflowStage.PARSED,
WorkflowStage.PARSED: WorkflowStage.REQUIREMENTS_READY,
WorkflowStage.REQUIREMENTS_READY: WorkflowStage.IR_READY,
~~~

Add:

~~~python
@property
def authoring_requirements(self) -> Path:
    return self.source_dir / "authoring-requirements.json"
~~~

Add validate_requirements before validate_ir:

~~~python
@app.command()
def validate_requirements(
    workspace: str = typer.Argument(..., help="Workspace directory"),
) -> None:
    """Validate confirmed authoring requirements for this source PDF."""
    from paperflow.paths import WorkspacePaths
    from paperflow.requirements.validator import validate_requirements_file
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
    errors = [issue for issue in issues if issue.severity == "error"]
    write_json(
        paths.qa_dir / "requirements-validation.json",
        {"passed": not errors, "issues": [issue.model_dump(mode="json") for issue in issues]},
    )
    if errors or requirements is None:
        typer.echo(f"Requirements invalid: {len(errors)} error(s)")
        for error in errors:
            typer.echo(f"  [{error.code}] {error.message}")
        raise typer.Exit(code=4)

    if manifest.stage == WorkflowStage.PARSED:
        advance_stage(ws, WorkflowStage.PARSED, WorkflowStage.REQUIREMENTS_READY)
    typer.echo("Requirements validation: PASS")
    typer.echo("Stage: requirements_ready")
    typer.echo("Next: author source/paper-ir.json and run paperflow validate-ir.")
~~~

Replace the validate_ir stage guard with:

~~~python
if manifest.stage not in (
    WorkflowStage.REQUIREMENTS_READY,
    WorkflowStage.IR_READY,
):
    raise InvalidStageError(
        "Expected stage 'requirements_ready' but workspace is at "
        f"'{manifest.stage.value}'. Run paperflow validate-requirements first."
    )
~~~

Replace its unconditional stage advance with:

~~~python
if manifest.stage == WorkflowStage.REQUIREMENTS_READY:
    advance_stage(
        ws,
        WorkflowStage.REQUIREMENTS_READY,
        WorkflowStage.IR_READY,
    )
~~~

Change the build_evidence accepted stages to:

~~~python
if manifest.stage not in (
    WorkflowStage.PARSED,
    WorkflowStage.REQUIREMENTS_READY,
    WorkflowStage.IR_READY,
):
    raise InvalidStageError(
        f"Expected a parsed workspace but workspace is at '{manifest.stage.value}'."
    )
~~~

Replace the parse completion message with:

~~~python
typer.echo(
    "Next: run paperflow build-evidence, complete the Skill requirements "
    "interview, and run paperflow validate-requirements."
)
~~~

Replace the build-evidence completion message with:

~~~python
typer.echo(
    "Next: complete the Skill requirements interview, write "
    "source/authoring-requirements.json, and run paperflow validate-requirements."
)
~~~

- [ ] **Step 4: Run focused tests**

~~~bash
uv run pytest tests/unit/test_paths.py tests/unit/test_manifest.py tests/unit/test_cli.py -q
~~~

Expected: all tests pass.

- [ ] **Step 5: Commit**

~~~bash
git add src/paperflow/models/common.py src/paperflow/manifest.py src/paperflow/paths.py src/paperflow/cli.py tests/unit/test_manifest.py tests/unit/test_paths.py tests/unit/test_cli.py
git commit -m "feat: enforce requirements workflow gate"
~~~

### Task 4: Skill intake protocol

**Files:**
- Create: skills/icml-paper-to-report-deck/references/requirements-intake.md
- Modify: skills/icml-paper-to-report-deck/SKILL.md
- Modify: skills/icml-paper-to-report-deck/references/workflow-contract.md
- Modify: tests/unit/test_skill_contract.py

**Interfaces:**
- The existing skill reads requirements-intake.md after parse and evidence generation.
- The skill cannot author Paper IR until validate-requirements passes.

- [ ] **Step 1: Write failing skill contract tests**

Add this helper and these tests:

~~~python
def _requirements_reference_text() -> str:
    path = (
        Path(__file__).parent.parent.parent
        / "skills"
        / "icml-paper-to-report-deck"
        / "references"
        / "requirements-intake.md"
    )
    return path.read_text(encoding="utf-8") if path.exists() else ""


def test_skill_requires_authoring_intake_gate() -> None:
    text = _skill_text().lower()
    assert "requirements-intake.md" in text
    assert "validate-requirements" in text
    assert "authoring-requirements.json" in text
    assert text.index("validate-requirements") < text.index("validate-ir")


def test_intake_reference_has_required_behavior() -> None:
    text = _requirements_reference_text().lower()
    phrases = [
        "one question at a time",
        "adaptive follow-up",
        "explicit confirmation",
        "do not author",
        "content_sha256",
        "pdf_sha256",
        "never request or persist",
        "do not write a markdown requirements copy",
    ]
    for phrase in phrases:
        assert phrase in text


def test_intake_reference_covers_all_core_topics() -> None:
    text = _requirements_reference_text().lower()
    topics = [
        "use scenario",
        "target audience",
        "report",
        "presentation",
        "content priorities",
        "technical depth",
        "language",
        "visual",
        "template",
        "evidence",
    ]
    for topic in topics:
        assert topic in text
~~~

- [ ] **Step 2: Run and verify the missing-reference failure**

~~~bash
uv run pytest tests/unit/test_skill_contract.py -q
~~~

Expected: failures because the reference and gate are absent.

- [ ] **Step 3: Create the reference and update the skill**

requirements-intake.md must contain:

~~~markdown
# Authoring Requirements Intake

## Hard Gate
Ask one question at a time after parse and evidence generation. Do not author paper-ir.json, report prose, storyboard content, or rendered artifacts until paperflow validate-requirements passes.

## Fixed Core Topics
Cover use scenario, target audience, report, presentation, content priorities, technical depth, language, visual direction, template and brand constraints, and evidence and delivery boundaries.

## Adaptive Follow-up
Ask an adaptive follow-up for ambiguity, contradiction, or a paper-specific choice. Recommend a default only when the user does not know, explain its effect, and record it as an assumption after acceptance.

## Summary and Explicit Confirmation
Show one complete summary after every topic is resolved. Require explicit confirmation. Silence and earlier partial approvals do not count.

## JSON and Digest
After confirmation, write only source/authoring-requirements.json. Do not write a Markdown requirements copy. Copy source.pdf_sha256 from manifest.json. Use compute_requirements_digest for confirmation.content_sha256. Run validate-requirements and continue only after PASS.

## Resume and Safety
Reuse a valid confirmed record for the same PDF. Re-interview unresolved or invalid fields and reconfirm edits. Never request or persist credentials, API keys, tokens, passwords, or unrelated personal information.
~~~

Insert this section in SKILL.md after evidence generation and before Paper IR authoring:

~~~markdown
### 3. Authoring Requirements Intake

Read references/requirements-intake.md completely. Ask one question at a time, resolve all fixed and adaptive topics, present the complete summary, and obtain explicit confirmation. Then write source/authoring-requirements.json and run:

    uv run paperflow validate-requirements .work/<paper-name>

Do not begin Paper IR authoring until this command passes and the workspace reaches requirements_ready. Both report and slide authoring must read source/authoring-requirements.json and source/paper-ir.json.
~~~

Renumber the remaining workflow sections. Add validate-requirements to the required command list and completion description.

Replace the workflow-contract.md state line with:

~~~text
INITIALIZED -> PARSED -> REQUIREMENTS_READY -> IR_READY -> REPORT_READY -> STORYBOARD_READY -> RENDERED -> CONTENT_QA_PASSED -> VISUAL_QA_PASSED -> FINALIZED
~~~

Replace the PARSED command rows with:

~~~markdown
| PARSED | Skill completes the requirements interview | Ask one question at a time and obtain explicit confirmation |
| PARSED | paperflow validate-requirements WORKSPACE | Validate authoring-requirements.json -> REQUIREMENTS_READY |
| REQUIREMENTS_READY | Skill authors paper-ir.json | Semantic interpretation from confirmed requirements and evidence |
| REQUIREMENTS_READY | paperflow validate-ir WORKSPACE | Validate IR -> IR_READY |
~~~

- [ ] **Step 4: Run skill contract tests**

~~~bash
uv run pytest tests/unit/test_skill_contract.py -q
~~~

Expected: all tests pass.

- [ ] **Step 5: Commit**

~~~bash
git add skills/icml-paper-to-report-deck/SKILL.md skills/icml-paper-to-report-deck/references/requirements-intake.md skills/icml-paper-to-report-deck/references/workflow-contract.md tests/unit/test_skill_contract.py
git commit -m "feat: add mandatory authoring intake skill"
~~~

### Task 5: Lifecycle, documentation, and verification

**Files:**
- Modify: tests/integration/test_end_to_end.py
- Modify: README.md
- Modify: docs/architecture.md

**Interfaces:**
- Full lifecycle validates requirements before Paper IR.
- Public docs show the exact state and command sequence.

- [ ] **Step 1: Update the integration lifecycle**

Add these imports to tests/integration/test_end_to_end.py:

~~~python
from paperflow.requirements.validator import validate_requirements_file
from tests.fixtures.make_authoring_requirements import make_authoring_requirements
~~~

After evidence generation and before Paper IR injection:

~~~python
requirements_data = make_authoring_requirements(manifest.source_sha256)
write_json(ws_paths.authoring_requirements, requirements_data)
requirements, requirement_issues = validate_requirements_file(
    ws_paths.authoring_requirements,
    manifest.source_sha256,
)
assert requirements is not None
assert requirement_issues == []
advance_stage(ws, WorkflowStage.PARSED, WorkflowStage.REQUIREMENTS_READY)
~~~

Replace the Paper IR transition with:

~~~python
advance_stage(
    ws,
    WorkflowStage.REQUIREMENTS_READY,
    WorkflowStage.IR_READY,
)
~~~

- [ ] **Step 2: Run integration tests**

~~~bash
uv run pytest tests/integration/test_end_to_end.py -q
~~~

Expected: all tests pass with the new stage in the lifecycle.

- [ ] **Step 3: Update README and architecture**

Add this sequence to README before the Paper IR step:

~~~markdown
After parsing and evidence extraction, the project skill asks one requirements question at a time. It covers the fixed core topics, asks paper-specific follow-ups, presents one complete summary, and requires explicit confirmation before writing source/authoring-requirements.json.

    paperflow validate-requirements WORKSPACE

The report and presentation both consume the confirmed authoring requirements and the canonical paper-ir.json. A parsed workspace cannot validate a Paper IR until requirements validation reaches requirements_ready.
~~~

Add validate-requirements to the README command list between build-evidence and validate-ir.

Replace the architecture state machine with:

~~~text
INITIALIZED -> PARSED -> REQUIREMENTS_READY -> IR_READY -> REPORT_READY
    -> STORYBOARD_READY -> RENDERED -> CONTENT_QA_PASSED
    -> VISUAL_QA_PASSED -> FINALIZED
~~~

Add this architecture contract:

~~~markdown
## Authoring Requirements Gate

The project skill owns conversational intake and asks one question at a time. Deterministic code validates source/authoring-requirements.json; it does not interview the user or invent missing answers. confirmation.content_sha256 binds the confirmation to canonical requirements content, and source.pdf_sha256 binds the record to manifest.json. Missing, invalid, edited, or wrong-paper requirements produce qa/requirements-validation.json and leave the workflow stage unchanged.
~~~

- [ ] **Step 4: Run full verification**

~~~bash
uv run pytest -q
pnpm --dir slides test
uv run ruff check .
uv run mypy src
pnpm --dir slides build
~~~

Expected: all Python and Vitest tests pass, Ruff has no errors, mypy has no issues, and TypeScript compilation succeeds.

- [ ] **Step 5: Run CLI smoke and secret checks**

Use a temporary directory outside the repository. Run init and parse on the sample PDF, verify validate-ir is rejected from parsed, write a sealed fixture record, run validate-requirements, and confirm status reports requirements_ready.

Run:

~~~bash
rg -n --hidden -g '!.git/**' -g '!uv.lock' '(ghp_|github_pat_|sk-[A-Za-z0-9_-]{20,}|MINERU_API_KEY\s*=)' .
~~~

Expected: no real credential. Documentation may mention MINERU_API_KEY without assigning a value.

- [ ] **Step 6: Commit documentation and lifecycle coverage**

~~~bash
git add tests/integration/test_end_to_end.py README.md docs/architecture.md
git commit -m "docs: document authoring requirements gate"
~~~

- [ ] **Step 7: Request review and verify clean state**

Use superpowers:requesting-code-review. Address all Critical and Important findings, rerun focused tests after each correction, then rerun Step 4. Finish with:

~~~bash
git status --short --branch
git log -6 --oneline --decorate
~~~

Expected: clean worktree, all implementation commits present, and no required work remaining.
