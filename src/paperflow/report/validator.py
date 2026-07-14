import re
from pathlib import Path

from paperflow.models.common import Severity
from paperflow.models.paper_ir import EvidenceRef
from paperflow.models.qa import ValidationIssue

_PLACEHOLDER_RE = re.compile(
    r"(?i)\b(TODO|TBD|XXXX|lorem ipsum|placeholder|insert (figure|text)|待补充|示例文本)\b"
)

_EVIDENCE_COMMENT_RE = re.compile(r"<!--\s*evidence:\s*([^>]+)\s*-->")

_REQUIRED_SECTIONS = [
    "论文信息",
    "执行摘要",
    "研究背景与实际问题",
    "现有方法与关键缺口",
    "核心观点与贡献",
    "方法总体框架",
    "关键模块与公式解释",
    "实验设计",
    "主要实验结果",
    "消融实验与机制分析",
    "创新性与优点",
    "局限性与潜在风险",
    "可复现性分析",
    "对后续研究的启示",
    "讨论问题",
    "证据索引",
]


def validate_report_qmd(
    qmd_path: Path, evidence: list[EvidenceRef]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    content = qmd_path.read_text(encoding="utf-8")

    ev_ids = {ev.id for ev in evidence}

    _check_required_sections(content, issues)
    _check_placeholders(content, issues)
    _check_evidence_refs(content, ev_ids, issues)

    return issues


def _check_required_sections(content: str, issues: list[ValidationIssue]) -> None:
    for section_title in _REQUIRED_SECTIONS:
        if f"# {section_title}" not in content and f"## {section_title}" not in content:
            issues.append(
                ValidationIssue(
                    code="REPORT_MISSING_SECTION",
                    severity=Severity.ERROR,
                    message=f"Required section '{section_title}' not found.",
                    location=f"section:{section_title}",
                )
            )


def _check_placeholders(content: str, issues: list[ValidationIssue]) -> None:
    for match in _PLACEHOLDER_RE.finditer(content):
        issues.append(
            ValidationIssue(
                code="REPORT_PLACEHOLDER_TEXT",
                severity=Severity.ERROR,
                message=f"Placeholder text found: '{match.group(0)}'",
                location=f"offset:{match.start()}",
            )
        )


def _check_evidence_refs(
    content: str, ev_ids: set[str], issues: list[ValidationIssue]
) -> None:
    for match in _EVIDENCE_COMMENT_RE.finditer(content):
        refs_text = match.group(1).strip()
        if refs_text == "TODO":
            continue
        for ref in refs_text.split(","):
            ref = ref.strip()
            if ref and ref not in ev_ids:
                issues.append(
                    ValidationIssue(
                        code="REPORT_UNKNOWN_EVIDENCE",
                        severity=Severity.ERROR,
                        message=f"Unknown evidence reference: '{ref}'",
                        location=f"offset:{match.start()}",
                    )
                )
