from pathlib import Path

from paperflow.ingest.asset_extractor import (
    AssetExtractor,
    extract_page_images,
)
from paperflow.ingest.pymupdf_parser import PyMuPDFParser
from tests.fixtures.make_sample_pdf import make_sample_pdf


def _sample_pdf_and_ws(tmp_path: Path) -> tuple[Path, Path]:
    pdf_path = tmp_path / "sample.pdf"
    make_sample_pdf(pdf_path)
    ws = tmp_path / "ws"
    return pdf_path, ws


def test_page_images_at_150_dpi(tmp_path: Path) -> None:
    pdf_path, ws = _sample_pdf_and_ws(tmp_path)
    page_dir = ws / "assets" / "page-images"
    page_dir.mkdir(parents=True, exist_ok=True)

    paths = extract_page_images(pdf_path, page_dir, dpi=150)
    assert len(paths) == 2
    for p in paths:
        assert p.exists()
        assert p.suffix == ".png"
        assert p.name == f"page-{paths.index(p) + 1:03d}.png"


def test_extractor_records_caption_candidates(tmp_path: Path) -> None:
    pdf_path, ws = _sample_pdf_and_ws(tmp_path)
    parser = PyMuPDFParser()
    doc = parser.parse(pdf_path, ws)

    extractor = AssetExtractor(pdf_path, ws)
    assets = extractor.extract(doc)

    captions = [a for a in assets if a.caption is not None]
    assert len(captions) >= 1


def test_asset_ids_are_unique(tmp_path: Path) -> None:
    pdf_path, ws = _sample_pdf_and_ws(tmp_path)
    parser = PyMuPDFParser()
    doc = parser.parse(pdf_path, ws)

    extractor = AssetExtractor(pdf_path, ws)
    assets = extractor.extract(doc)

    ids = [a.id for a in assets]
    assert len(ids) == len(set(ids))


def test_asset_paths_are_relative(tmp_path: Path) -> None:
    pdf_path, ws = _sample_pdf_and_ws(tmp_path)
    parser = PyMuPDFParser()
    doc = parser.parse(pdf_path, ws)

    extractor = AssetExtractor(pdf_path, ws)
    assets = extractor.extract(doc)

    for a in assets:
        assert not Path(a.file_path).is_absolute()
        full_path = ws / a.file_path
        assert full_path.exists()
