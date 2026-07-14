from pathlib import Path

from paperflow.report.scaffold import scaffold_outline, scaffold_qmd


def test_scaffold_outline_has_required_sections() -> None:
    outline = scaffold_outline("Test Paper Title")
    assert outline.schema_version == "1.0"
    assert outline.title == "Test Paper Title"
    section_titles = {s.title for s in outline.sections}
    assert "执行摘要" in section_titles
    assert "核心观点与贡献" in section_titles
    assert "主要实验结果" in section_titles
    assert "局限性与潜在风险" in section_titles


def test_scaffold_outline_section_count_in_range() -> None:
    outline = scaffold_outline("Test")
    assert 10 <= len(outline.sections) <= 20


def test_scaffold_qmd_contains_section_headings(tmp_path: Path) -> None:
    outline = scaffold_outline("Test Paper")
    qmd_path = tmp_path / "report.qmd"
    scaffold_qmd(outline, qmd_path)
    content = qmd_path.read_text(encoding="utf-8")
    for section in outline.sections:
        assert section.title in content


def test_scaffold_qmd_has_title_block(tmp_path: Path) -> None:
    outline = scaffold_outline("Test Paper")
    qmd_path = tmp_path / "report.qmd"
    scaffold_qmd(outline, qmd_path)
    content = qmd_path.read_text(encoding="utf-8")
    assert "Test Paper" in content
