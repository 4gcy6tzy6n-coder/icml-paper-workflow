import re
from pathlib import Path

from paperflow.ingest.pymupdf_parser import PyMuPDFParser


def _sample_pdf(tmp_path: Path) -> Path:
    from tests.fixtures.make_sample_pdf import make_sample_pdf

    pdf_path = tmp_path / "sample.pdf"
    make_sample_pdf(pdf_path)
    return pdf_path


def test_parser_is_available() -> None:
    parser = PyMuPDFParser()
    assert parser.available() is True
    assert parser.name == "pymupdf"


def test_page_count(tmp_path: Path) -> None:
    parser = PyMuPDFParser()
    doc = parser.parse(_sample_pdf(tmp_path), tmp_path / "ws")
    assert doc.page_count == 2


def test_text_blocks_have_stable_ids(tmp_path: Path) -> None:
    parser = PyMuPDFParser()
    doc = parser.parse(_sample_pdf(tmp_path), tmp_path / "ws")
    ids = [b.id for b in doc.blocks]
    for bid in ids:
        assert re.match(r"^p\d{2}-b\d{3}$", bid), f"Invalid block ID: {bid}"


def test_every_block_has_page_and_non_empty_text(tmp_path: Path) -> None:
    parser = PyMuPDFParser()
    doc = parser.parse(_sample_pdf(tmp_path), tmp_path / "ws")
    for block in doc.blocks:
        assert block.page >= 1
        assert len(block.text) > 0


def test_markdown_contains_page_anchors(tmp_path: Path) -> None:
    parser = PyMuPDFParser()
    doc = parser.parse(_sample_pdf(tmp_path), tmp_path / "ws")
    md_path = Path(doc.markdown_path)
    md_text = md_path.read_text(encoding="utf-8")
    assert "<!-- page:1 -->" in md_text
    assert "<!-- page:2 -->" in md_text


def test_stable_output_across_two_runs(tmp_path: Path) -> None:
    pdf = _sample_pdf(tmp_path)
    doc1 = PyMuPDFParser().parse(pdf, tmp_path / "ws1")
    doc2 = PyMuPDFParser().parse(pdf, tmp_path / "ws2")
    assert len(doc1.blocks) == len(doc2.blocks)
    for b1, b2 in zip(doc1.blocks, doc2.blocks, strict=True):
        assert b1.id == b2.id
        assert b1.text == b2.text


def test_empty_page_produces_warning(tmp_path: Path) -> None:
    import fitz

    pdf = _sample_pdf(tmp_path)
    parser = PyMuPDFParser()

    doc = fitz.open(pdf)
    doc.new_page(width=612, height=792)
    empty_pdf = tmp_path / "with_empty.pdf"
    doc.save(str(empty_pdf))
    doc.close()

    parsed = parser.parse(empty_pdf, tmp_path / "ws")
    assert parsed.page_count == 3
