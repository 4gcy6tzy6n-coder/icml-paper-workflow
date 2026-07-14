from pathlib import Path

from paperflow.models.report import ReportOutline, ReportSectionPlan

_REQUIRED_SECTIONS = [
    ("sec-info", "论文信息", "Document paper metadata", 100),
    ("sec-summary", "执行摘要", "Summarize the paper in one paragraph", 200),
    ("sec-background", "研究背景与实际问题", "Describe the research context", 400),
    ("sec-gap", "现有方法与关键缺口", "Identify gaps in prior work", 400),
    ("sec-contributions", "核心观点与贡献", "List the main contributions", 350),
    ("sec-method", "方法总体框架", "Overview the proposed method", 500),
    ("sec-modules", "关键模块与公式解释", "Explain key components and formulas", 500),
    ("sec-exp-design", "实验设计", "Describe experimental setup", 400),
    ("sec-results", "主要实验结果", "Present headline results", 600),
    ("sec-ablation", "消融实验与机制分析", "Analyze ablations and mechanisms", 500),
    ("sec-novelty", "创新性与优点", "Discuss novelty and strengths", 350),
    ("sec-limitations", "局限性与潜在风险", "Discuss limitations honestly", 400),
    ("sec-repro", "可复现性分析", "Assess reproducibility", 300),
    ("sec-implications", "对后续研究的启示", "Implications for future work", 350),
    ("sec-discussion", "讨论问题", "Open discussion questions", 200),
    ("sec-evidence", "证据索引", "Evidence index by section", 150),
]


def scaffold_outline(title: str) -> ReportOutline:
    sections = [
        ReportSectionPlan(
            section_id=sid,
            title=stitle,
            purpose=spurpose,
            evidence_ids=[],
            target_words=swords,
        )
        for sid, stitle, spurpose, swords in _REQUIRED_SECTIONS
    ]
    return ReportOutline(
        schema_version="1.0",
        title=title,
        sections=sections,
    )


def scaffold_qmd(outline: ReportOutline, output_path: Path) -> None:
    lines: list[str] = []
    lines.append("---")
    lines.append(f'title: "{outline.title}"')
    lines.append("format:")
    lines.append("  docx:")
    lines.append("    toc: true")
    lines.append("    number-sections: true")
    lines.append("lang: zh-CN")
    lines.append("---\n")

    for section in outline.sections:
        lines.append(f"# {section.title}\n")
        lines.append(
            f"<!-- section_id: {section.section_id} "
            f"target_words: {section.target_words} -->\n"
        )
        lines.append("<!-- evidence: TODO -->\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
