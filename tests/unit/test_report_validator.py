from pathlib import Path

from paperflow.models.paper_ir import EvidenceRef
from paperflow.report.validator import validate_report_qmd


def _sample_evidence() -> list[EvidenceRef]:
    return [
        EvidenceRef(
            id="ev-p01-b001",
            page=1,
            block_id="p01-b001",
            source_text="A novel method.",
        ),
        EvidenceRef(
            id="ev-p01-b002",
            page=1,
            block_id="p01-b002",
            source_text="We achieve 87.4% accuracy.",
        ),
    ]


def _report_with_all_sections(tmp_path: Path) -> Path:
    sections = "\n\n".join(
        f"# {title}\n\nSection content.\n<!-- evidence: ev-p01-b001 -->"
        for title in [
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
    )
    qmd = tmp_path / "report.qmd"
    qmd.write_text(
        f"""---
title: "Test Paper"
---

{sections}
""",
        encoding="utf-8",
    )
    return qmd


def test_valid_report_passes(tmp_path: Path) -> None:
    qmd = _report_with_all_sections(tmp_path)
    issues = validate_report_qmd(qmd, _sample_evidence())
    errors = [i for i in issues if i.severity == "error"]
    assert len(errors) == 0


def test_missing_required_section_detected(tmp_path: Path) -> None:
    qmd = tmp_path / "report.qmd"
    qmd.write_text(
        """---
title: "Minimal"
---

# 执行摘要

No other sections.
<!-- evidence: ev-p01-b001 -->
""",
        encoding="utf-8",
    )
    issues = validate_report_qmd(qmd, _sample_evidence())
    codes = {i.code for i in issues}
    assert "REPORT_MISSING_SECTION" in codes


def test_placeholder_detected(tmp_path: Path) -> None:
    qmd = tmp_path / "report.qmd"
    qmd.write_text(
        """---
title: "Test"
---

# 执行摘要

TBD: fill this in later.
<!-- evidence: ev-p01-b001 -->
""",
        encoding="utf-8",
    )
    issues = validate_report_qmd(qmd, _sample_evidence())
    codes = {i.code for i in issues}
    assert "REPORT_PLACEHOLDER_TEXT" in codes


def test_unknown_evidence_detected(tmp_path: Path) -> None:
    qmd = tmp_path / "report.qmd"
    qmd.write_text(
        """---
title: "Test"
---

# 执行摘要

Some text.
<!-- evidence: ev-nonexistent -->
""",
        encoding="utf-8",
    )
    issues = validate_report_qmd(qmd, _sample_evidence())
    codes = {i.code for i in issues}
    assert "REPORT_UNKNOWN_EVIDENCE" in codes
