"""Placeholder detection for all artifact types."""

import re
from pathlib import Path

from paperflow.models.common import Severity
from paperflow.models.qa import ValidationIssue

_PLACEHOLDER_RE = re.compile(
    r"(?i)\b(TODO|TBD|XXXX|lorem ipsum|placeholder"
    r"|insert (figure|text)|待补充|示例文本)\b"
)


def scan_file_for_placeholders(path: Path) -> list[ValidationIssue]:
    """Scan a file for placeholder text patterns."""
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    issues: list[ValidationIssue] = []
    for match in _PLACEHOLDER_RE.finditer(content):
        issues.append(
            ValidationIssue(
                code="REPORT_PLACEHOLDER_TEXT",
                severity=Severity.ERROR,
                message=f"Placeholder '{match.group(0)}' found in {path.name}",
                location=f"{path.name}:offset:{match.start()}",
            )
        )
    return issues
