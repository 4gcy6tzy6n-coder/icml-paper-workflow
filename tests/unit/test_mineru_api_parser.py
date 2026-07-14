import io
import json
import zipfile
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.request import Request

import pytest

from paperflow.errors import ExternalToolError
from paperflow.ingest.mineru_api_parser import MinerUApiParser
from paperflow.util.hashing import sha256_file


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self._body if size < 0 else self._body[:size]


def _json_response(payload: dict[str, Any]) -> _Response:
    return _Response(json.dumps(payload).encode("utf-8"))


def _result_zip(*, include_json: bool = True) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("paper/full.md", "First block\n\nSecond block")
        if include_json:
            archive.writestr(
                "paper/paper_content_list.json",
                json.dumps(
                    [
                        {"type": "text", "text": "First block", "page_idx": 0},
                        {"type": "text", "text": "Second block", "page_idx": 1},
                    ]
                ),
            )
    return buffer.getvalue()


def _pdf(tmp_path: Path) -> Path:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\nfixture\n")
    return pdf


def _success_opener(
    archive_bytes: bytes,
) -> tuple[Any, list[Request]]:
    requests: list[Request] = []
    poll_count = 0

    def opener(request: Request, timeout: int) -> _Response:
        nonlocal poll_count
        requests.append(request)
        url = request.full_url
        method = request.get_method()
        assert timeout == 60
        if method == "POST" and url.endswith("/file-urls/batch"):
            return _json_response(
                {
                    "code": 0,
                    "data": {
                        "batch_id": "batch-123",
                        "file_urls": ["https://uploads.example/paper.pdf"],
                    },
                    "msg": "ok",
                }
            )
        if method == "GET" and url.endswith("/extract-results/batch/batch-123"):
            poll_count += 1
            state = "running" if poll_count == 1 else "done"
            result: dict[str, Any] = {"file_name": "paper.pdf", "state": state}
            if state == "done":
                result["full_zip_url"] = "https://downloads.example/result.zip"
            return _json_response(
                {
                    "code": 0,
                    "data": {"batch_id": "batch-123", "extract_result": [result]},
                    "msg": "ok",
                }
            )
        if method == "GET" and url == "https://downloads.example/result.zip":
            return _Response(archive_bytes)
        raise AssertionError(f"unexpected request: {method} {url}")

    return opener, requests


def test_api_parser_is_unavailable_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MINERU_API_KEY", raising=False)

    assert MinerUApiParser().available() is False


def test_api_error_never_echoes_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-secret")

    def failing_opener(*args: object, **kwargs: object) -> object:
        raise OSError("network unavailable")

    with pytest.raises(ExternalToolError) as exc:
        MinerUApiParser(opener=failing_opener).parse(
            _pdf(tmp_path), tmp_path / "workspace"
        )

    assert "test-secret" not in str(exc.value)


def test_parse_uploads_downloads_and_normalizes_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")
    opener, requests = _success_opener(_result_zip())
    workspace = tmp_path / "workspace"
    uploads: list[tuple[str, bytes, float]] = []

    def uploader(url: str, path: Path, timeout: float) -> None:
        uploads.append((url, path.read_bytes(), timeout))

    document = MinerUApiParser(
        opener=opener,
        uploader=uploader,
        sleeper=lambda _: None,
    ).parse(_pdf(tmp_path), workspace)

    assert document.parser_name == "mineru_api"
    assert [block.id for block in document.blocks] == ["p01-b001", "p02-b002"]
    assert [block.text for block in document.blocks] == ["First block", "Second block"]
    assert document.page_count == 2
    assert (workspace / "source" / "mineru-api" / "result.zip").read_bytes()
    assert (
        workspace
        / "source"
        / "mineru-api"
        / "extracted"
        / "paper"
        / "paper_content_list.json"
    ).exists()
    assert (workspace / "source" / "parsed-paper.md").exists()
    assert (workspace / "source" / "parsed-document.json").exists()

    assert uploads == [
        ("https://uploads.example/paper.pdf", b"%PDF-1.4\nfixture\n", 60)
    ]
    assert all(request.get_method() != "PUT" for request in requests)


def test_each_parse_uses_unique_data_id_for_same_pdf(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")
    pdf = _pdf(tmp_path)
    opener_one, requests_one = _success_opener(_result_zip())
    opener_two, requests_two = _success_opener(_result_zip())

    MinerUApiParser(
        opener=opener_one,
        uploader=lambda *_: None,
        sleeper=lambda _: None,
    ).parse(pdf, tmp_path / "workspace-one")
    MinerUApiParser(
        opener=opener_two,
        uploader=lambda *_: None,
        sleeper=lambda _: None,
    ).parse(pdf, tmp_path / "workspace-two")

    def data_id(requests: list[Request]) -> str:
        post = next(request for request in requests if request.get_method() == "POST")
        assert post.data is not None
        payload = json.loads(post.data.decode("utf-8"))
        return str(payload["files"][0]["data_id"])

    first_id = data_id(requests_one)
    second_id = data_id(requests_two)
    assert first_id != second_id
    pdf_sha256 = sha256_file(pdf)
    for value in (first_id, second_id):
        assert len(value) == 97
        assert len(value) <= 128
        prefix, suffix = value.rsplit("-", 1)
        assert prefix == pdf_sha256
        assert len(suffix) == 32
        assert all(character in "0123456789abcdef" for character in suffix)


def test_parse_rejects_archive_without_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")
    opener, _ = _success_opener(_result_zip(include_json=False))

    with pytest.raises(ExternalToolError, match="no JSON"):
        MinerUApiParser(
            opener=opener,
            uploader=lambda *_: None,
            sleeper=lambda _: None,
        ).parse(_pdf(tmp_path), tmp_path / "workspace")


def test_parse_reports_failed_remote_task(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")

    def opener(request: Request, timeout: int) -> _Response:
        if request.get_method() == "POST":
            return _json_response(
                {
                    "code": 0,
                    "data": {
                        "batch_id": "batch-failed",
                        "file_urls": ["https://uploads.example/paper.pdf"],
                    },
                }
            )
        return _json_response(
            {
                "code": 0,
                "data": {
                    "extract_result": [
                        {
                            "file_name": "paper.pdf",
                            "state": "failed",
                            "err_msg": "unsupported document format",
                        }
                    ]
                },
            }
        )

    with pytest.raises(ExternalToolError, match="failed.*unsupported document format"):
        MinerUApiParser(
            opener=opener,
            uploader=lambda *_: None,
            sleeper=lambda _: None,
        ).parse(_pdf(tmp_path), tmp_path / "workspace")


def test_parse_times_out(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")

    def opener(request: Request, timeout: int) -> _Response:
        if request.get_method() == "POST":
            return _json_response(
                {
                    "code": 0,
                    "data": {
                        "batch_id": "batch-slow",
                        "file_urls": ["https://uploads.example/paper.pdf"],
                    },
                }
            )
        return _json_response(
            {
                "code": 0,
                "data": {
                    "extract_result": [
                        {"file_name": "paper.pdf", "state": "running"}
                    ]
                },
            }
        )

    with pytest.raises(ExternalToolError, match="timed out.*batch-slow"):
        MinerUApiParser(
            opener=opener,
            uploader=lambda *_: None,
            sleeper=lambda _: None,
            max_poll_attempts=2,
        ).parse(_pdf(tmp_path), tmp_path / "workspace")


def test_poll_timeout_is_a_wall_clock_deadline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")
    times = iter([0.0, 0.0, 121.0])

    def opener(request: Request, timeout: float) -> _Response:
        if request.get_method() == "POST":
            return _json_response(
                {
                    "code": 0,
                    "data": {
                        "batch_id": "batch-deadline",
                        "file_urls": ["https://uploads.example/paper.pdf"],
                    },
                }
            )
        return _json_response(
            {
                "code": 0,
                "data": {
                    "extract_result": [
                        {"file_name": "paper.pdf", "state": "running"}
                    ]
                },
            }
        )

    with pytest.raises(ExternalToolError, match="timed out.*batch-deadline"):
        MinerUApiParser(
            opener=opener,
            uploader=lambda *_: None,
            sleeper=lambda _: None,
            clock=lambda: next(times),
            poll_timeout_seconds=120,
        ).parse(_pdf(tmp_path), tmp_path / "workspace")


def test_upload_transport_sends_pdf_content_type_without_authorization(
    tmp_path: Path,
) -> None:
    from paperflow.ingest.mineru_api_parser import _upload_file

    pdf = _pdf(tmp_path)
    headers: dict[str, str] = {}
    sent = bytearray()

    class UploadResponse:
        status = 200

        def read(self, size: int = -1) -> bytes:
            return b""

    class Connection:
        def putrequest(self, method: str, target: str, **kwargs: object) -> None:
            assert method == "PUT"
            assert target == "/paper.pdf?signature=abc"

        def putheader(self, name: str, value: str) -> None:
            headers[name.lower()] = value

        def endheaders(self) -> None:
            return None

        def send(self, data: bytes) -> None:
            sent.extend(data)

        def getresponse(self) -> UploadResponse:
            return UploadResponse()

        def close(self) -> None:
            return None

    def connection_factory(host: str, port: int | None, timeout: float) -> Connection:
        assert host == "uploads.example"
        assert port is None
        assert timeout == 60
        return Connection()

    _upload_file(
        "https://uploads.example/paper.pdf?signature=abc",
        pdf,
        60,
        connection_factory=connection_factory,
    )

    assert sent == pdf.read_bytes()
    assert headers["content-length"] == str(pdf.stat().st_size)
    assert headers["content-type"] == "application/pdf"
    assert "authorization" not in headers


def test_cross_origin_redirect_strips_authorization() -> None:
    from paperflow.ingest.mineru_api_parser import _SafeRedirectHandler

    request = Request(
        "https://mineru.net/api/v4/file-urls/batch",
        headers={"Authorization": "Bearer test-secret"},
    )
    redirected = _SafeRedirectHandler().redirect_request(
        request,
        None,
        302,
        "Found",
        Message(),
        "https://other.example/result",
    )

    assert redirected is not None
    assert redirected.get_header("Authorization") is None


def test_malformed_upload_response_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")

    with pytest.raises(ExternalToolError, match="missing a batch ID"):
        MinerUApiParser(
            opener=lambda *_args, **_kwargs: _json_response({"code": 0, "data": {}}),
            uploader=lambda *_: None,
        ).parse(_pdf(tmp_path), tmp_path / "workspace")


def test_invalid_result_zip_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")
    opener, _ = _success_opener(b"not-a-zip")

    with pytest.raises(ExternalToolError, match="invalid result archive"):
        MinerUApiParser(
            opener=opener,
            uploader=lambda *_: None,
            sleeper=lambda _: None,
        ).parse(_pdf(tmp_path), tmp_path / "workspace")


def test_unsafe_archive_path_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-key")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../outside.json", '[{"text": "unsafe"}]')
    opener, _ = _success_opener(buffer.getvalue())

    with pytest.raises(ExternalToolError, match="unsafe JSON path"):
        MinerUApiParser(
            opener=opener,
            uploader=lambda *_: None,
            sleeper=lambda _: None,
        ).parse(_pdf(tmp_path), tmp_path / "workspace")


def test_archive_total_json_size_is_bounded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import paperflow.ingest.mineru_api_parser as module

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("result.json", '[{"text": "content beyond limit"}]')
    monkeypatch.setattr(module, "_MAX_JSON_TOTAL_BYTES", 10)

    with pytest.raises(ExternalToolError, match="JSON exceeds the size limit"):
        MinerUApiParser._extract_json(buffer.getvalue(), tmp_path / "extracted")


def test_normalization_prefers_standard_content_list_over_v2(
    tmp_path: Path,
) -> None:
    standard = tmp_path / "paper_content_list.json"
    standard.write_text(
        json.dumps(
            [
                {"text": "Page one", "page_idx": 0},
                {"text": "Page two", "page_idx": 1},
            ]
        ),
        encoding="utf-8",
    )
    v2 = tmp_path / "paper_content_list_v2.json"
    v2.write_text(json.dumps([[{"text": "Duplicate"}]]), encoding="utf-8")

    blocks = MinerUApiParser._normalize_blocks([standard, v2])

    assert [block.text for block in blocks] == ["Page one", "Page two"]
    assert [block.page for block in blocks] == [1, 2]


def test_v2_content_list_uses_top_level_index_as_page_number(tmp_path: Path) -> None:
    v2 = tmp_path / "paper_content_list_v2.json"
    v2.write_text(
        json.dumps([[{"text": "Page one"}], [{"text": "Page two"}]]),
        encoding="utf-8",
    )

    blocks = MinerUApiParser._normalize_blocks([v2])

    assert [block.page for block in blocks] == [1, 2]


def test_empty_standard_content_list_falls_back_to_v2(tmp_path: Path) -> None:
    standard = tmp_path / "paper_content_list.json"
    standard.write_text("[]", encoding="utf-8")
    v2 = tmp_path / "paper_content_list_v2.json"
    v2.write_text(json.dumps([[{"text": "Recovered"}]]), encoding="utf-8")

    blocks = MinerUApiParser._normalize_blocks([standard, v2])

    assert [block.text for block in blocks] == ["Recovered"]


def test_malformed_standard_content_list_falls_back_to_v2(tmp_path: Path) -> None:
    standard = tmp_path / "paper_content_list.json"
    standard.write_text("not-json", encoding="utf-8")
    v2 = tmp_path / "paper_content_list_v2.json"
    v2.write_text(json.dumps([[{"text": "Recovered"}]]), encoding="utf-8")

    blocks = MinerUApiParser._normalize_blocks([standard, v2])

    assert [block.text for block in blocks] == ["Recovered"]
