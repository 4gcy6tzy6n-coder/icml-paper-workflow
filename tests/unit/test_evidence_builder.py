import re
from pathlib import Path

from paperflow.evidence.builder import build_evidence_map
from paperflow.ingest.pymupdf_parser import PyMuPDFParser
from tests.fixtures.make_sample_pdf import make_sample_pdf


def _parsed(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    make_sample_pdf(pdf)
    return PyMuPDFParser().parse(pdf, tmp_path / "ws")


def test_every_text_block_maps_to_an_evidence_ref(tmp_path: Path) -> None:
    doc = _parsed(tmp_path)
    evidence = build_evidence_map(doc)
    block_ids = {b.id for b in doc.blocks}
    ev_block_ids = {ref.block_id for ref in evidence}
    assert block_ids == ev_block_ids


def test_evidence_ids_follow_pattern(tmp_path: Path) -> None:
    doc = _parsed(tmp_path)
    evidence = build_evidence_map(doc)
    for ref in evidence:
        assert re.match(r"^ev-p\d{2,4}-b\d{3,5}(-[a-z])?$", ref.id), (
            f"Invalid evidence ID: {ref.id}"
        )


def test_source_text_preserved(tmp_path: Path) -> None:
    doc = _parsed(tmp_path)
    evidence = build_evidence_map(doc)
    for ref in evidence:
        assert len(ref.source_text) > 0
        assert len(ref.source_text) <= 2000


def test_page_and_block_references_are_stable(tmp_path: Path) -> None:
    doc1 = _parsed(tmp_path)
    tmp2 = tmp_path / "round2"
    tmp2.mkdir()
    doc2 = _parsed(tmp2)
    ev1 = build_evidence_map(doc1)
    ev2 = build_evidence_map(doc2)
    assert len(ev1) == len(ev2)
    for r1, r2 in zip(ev1, ev2, strict=True):
        assert r1.id == r2.id
        assert r1.page == r2.page
        assert r1.block_id == r2.block_id
