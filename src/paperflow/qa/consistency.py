import re
from pathlib import Path

from paperflow.models.common import Severity
from paperflow.models.paper_ir import Contribution, NumericResult
from paperflow.models.qa import QAResult, ValidationIssue

_PLACEHOLDER_RE = re.compile(
    r"(?i)\b(TODO|TBD|XXXX|lorem ipsum|placeholder"
    r"|insert (figure|text)|待补充|示例文本)\b"
)


def check_contribution_consistency(
    contributions: list[Contribution],
    expected_keywords: list[str],
) -> list[ValidationIssue]:
    """Check that expected contribution keywords appear in the IR."""
    issues: list[ValidationIssue] = []
    all_text = " ".join(c.statement.lower() for c in contributions)

    for kw in expected_keywords:
        if kw.lower() not in all_text:
            issues.append(
                ValidationIssue(
                    code="CONTRIBUTION_KEYWORD_MISMATCH",
                    severity=Severity.WARNING,
                    message=f"Expected contribution keyword '{kw}' not found.",
                    location="contributions",
                )
            )
    return issues


def check_numeric_alignment(
    results: list[NumericResult],
    expected_metrics: set[str],
) -> list[ValidationIssue]:
    """Check that metrics in both report and deck match the IR."""
    issues: list[ValidationIssue] = []
    ir_metrics = {r.metric for r in results}

    for metric in expected_metrics:
        if metric not in ir_metrics:
            issues.append(
                ValidationIssue(
                    code="METRIC_MISMATCH",
                    severity=Severity.WARNING,
                    message=f"Expected metric '{metric}' not found in numeric results.",
                    location="numeric_results",
                )
            )
    return issues


def check_placeholders(text: str, location: str = "") -> list[ValidationIssue]:
    """Scan text for placeholder patterns."""
    issues: list[ValidationIssue] = []
    for match in _PLACEHOLDER_RE.finditer(text):
        issues.append(
            ValidationIssue(
                code="REPORT_PLACEHOLDER_TEXT",
                severity=Severity.ERROR,
                message=f"Placeholder text found: '{match.group(0)}'",
                location=f"{location}:offset:{match.start()}",
            )
        )
    return issues


def check_cross_artifact_consistency(workspace: Path) -> QAResult:
    """Run cross-artifact consistency checks between report and slides."""
    from paperflow.models.paper_ir import PaperIR
    from paperflow.paths import WorkspacePaths
    from paperflow.util.jsonio import read_json

    ws_paths = WorkspacePaths(workspace)
    issues: list[ValidationIssue] = []

    if not ws_paths.paper_ir.exists():
        return QAResult(
            passed=False,
            issues=[
                ValidationIssue(
                    code="IR_MISSING_FILE",
                    severity=Severity.ERROR,
                    message="Paper IR not found.",
                )
            ],
        )

    ir_data = read_json(ws_paths.paper_ir)
    ir = PaperIR.model_validate(ir_data)

    # Check report for placeholders
    if ws_paths.report_qmd.exists():
        report_text = ws_paths.report_qmd.read_text(encoding="utf-8")
        issues.extend(check_placeholders(report_text, "report"))

    # Check storyboard for placeholders
    if ws_paths.storyboard.exists():
        sb_text = ws_paths.storyboard.read_text(encoding="utf-8")
        issues.extend(check_placeholders(sb_text, "storyboard"))

    # Evidence coverage
    ev_ids = {ev.id for ev in ir.evidence}
    all_evidence_refs: set[str] = set()

    for c in ir.contributions:
        all_evidence_refs.update(c.evidence_ids)
    for f in ir.findings:
        all_evidence_refs.update(f.evidence_ids)
    for nr in ir.numeric_results:
        all_evidence_refs.update(nr.evidence_ids)
    for lim in ir.limitations:
        all_evidence_refs.update(lim.evidence_ids)

    unknown = all_evidence_refs - ev_ids
    if unknown:
        issues.append(
            ValidationIssue(
                code="IR_UNKNOWN_EVIDENCE",
                severity=Severity.ERROR,
                message=f"Unknown evidence references: {', '.join(sorted(unknown))}",
            )
        )

    coverage = (
        len(all_evidence_refs & ev_ids) / len(all_evidence_refs)
        if all_evidence_refs
        else 1.0
    )

    errors = [i for i in issues if i.severity == "error"]
    return QAResult(
        passed=len(errors) == 0,
        issues=issues,
        metrics={"evidence_coverage": coverage},
    )
