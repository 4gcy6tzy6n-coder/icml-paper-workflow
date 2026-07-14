from pathlib import Path

import pytest

from paperflow.config import WorkflowConfig
from paperflow.errors import ExternalToolError
from paperflow.ingest.parser_chain import (
    FakeDocumentParser,
    parse_with_fallback,
    select_parser_chain,
)


def _dummy_pdf(tmp_path: Path) -> Path:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy\n")
    return pdf


def test_select_parser_chain_returns_pymupdf_by_default() -> None:
    config = WorkflowConfig()
    chain = select_parser_chain(config)
    assert len(chain) >= 1
    names = {p.name for p in chain}
    assert "pymupdf" in names


def test_api_parser_precedes_local_mineru_when_key_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")

    chain = select_parser_chain(WorkflowConfig())

    assert chain[0].name == "mineru_api"


def test_api_parser_is_not_duplicated_in_custom_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")
    config = WorkflowConfig(
        preferred_parser_order=["mineru_api", "mineru", "pymupdf"]
    )

    chain = select_parser_chain(config)

    assert [parser.name for parser in chain].count("mineru_api") == 1


def test_parse_with_fallback_first_succeeds(tmp_path: Path) -> None:
    avail = FakeDocumentParser("parser1", True)
    not_avail = FakeDocumentParser("parser2", False)
    doc, fallbacks, used_name = parse_with_fallback(
        _dummy_pdf(tmp_path), tmp_path / "ws", [avail, not_avail]
    )
    assert used_name == "parser1"
    assert doc.parser_name == "parser1"
    assert fallbacks == []


def test_parse_with_fallback_first_fails_second_succeeds(tmp_path: Path) -> None:
    failing = FakeDocumentParser("fail", True, should_fail=True)
    ok = FakeDocumentParser("ok", True)
    doc, fallbacks, used_name = parse_with_fallback(
        _dummy_pdf(tmp_path), tmp_path / "ws", [failing, ok]
    )
    assert used_name == "ok"
    assert fallbacks == ["fail"]


def test_unavailable_parser_is_skipped(tmp_path: Path) -> None:
    not_avail = FakeDocumentParser("ghost", False)
    ok = FakeDocumentParser("real", True)
    doc, fallbacks, used_name = parse_with_fallback(
        _dummy_pdf(tmp_path), tmp_path / "ws", [not_avail, ok]
    )
    assert used_name == "real"
    assert fallbacks == []


def test_parse_with_fallback_all_fail(tmp_path: Path) -> None:
    f1 = FakeDocumentParser("f1", True, should_fail=True)
    f2 = FakeDocumentParser("f2", True, should_fail=True)
    with pytest.raises(ExternalToolError) as exc:
        parse_with_fallback(_dummy_pdf(tmp_path), tmp_path / "ws", [f1, f2])
    assert "f1" in str(exc.value)
    assert "f2" in str(exc.value)
