"""MinerU Precision Extract API adapter."""

import http.client
import io
import json
import os
import time
import zipfile
from collections.abc import Callable, Iterator
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from paperflow.errors import ExternalToolError
from paperflow.models.document import ParsedDocument, TextBlock
from paperflow.util.hashing import sha256_file
from paperflow.util.jsonio import write_json

_API_ROOT = "https://mineru.net/api/v4"
_HTTP_TIMEOUT_SECONDS = 60
_POLL_TIMEOUT_SECONDS = 120
_MAX_API_RESPONSE_BYTES = 2 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
_MAX_JSON_FILES = 1_000
_MAX_JSON_MEMBER_BYTES = 64 * 1024 * 1024
_MAX_JSON_TOTAL_BYTES = 256 * 1024 * 1024
_MAX_COMPRESSION_RATIO = 1_000
_Opener = Callable[..., Any]
_Sleeper = Callable[[float], None]
_Clock = Callable[[], float]
_Uploader = Callable[[str, Path, float], None]
_ConnectionFactory = Callable[[str, int | None, float], Any]


class _SafeRedirectHandler(HTTPRedirectHandler):
    """Preserve auth only for same-origin HTTPS redirects."""

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> Request | None:
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            return None
        old_target = urlsplit(req.full_url)
        new_target = urlsplit(newurl)
        if new_target.scheme != "https":
            return None
        old_origin = (old_target.hostname, old_target.port or 443)
        new_origin = (new_target.hostname, new_target.port or 443)
        if old_origin != new_origin:
            redirected.remove_header("Authorization")
        return redirected


_SAFE_OPENER = build_opener(_SafeRedirectHandler())


def _safe_urlopen(request: Request, timeout: float) -> Any:
    return _SAFE_OPENER.open(request, timeout=timeout)


def _https_connection(host: str, port: int | None, timeout: float) -> Any:
    return http.client.HTTPSConnection(host, port=port, timeout=timeout)


def _upload_file(
    url: str,
    pdf_path: Path,
    timeout: float,
    *,
    connection_factory: _ConnectionFactory = _https_connection,
) -> None:
    """PUT raw bytes to a signed HTTPS URL without content type or auth headers."""
    target = urlsplit(url)
    if target.scheme != "https" or not target.hostname:
        raise ExternalToolError("MinerU API returned an invalid upload URL.")
    request_target = target.path or "/"
    if target.query:
        request_target = f"{request_target}?{target.query}"

    connection = connection_factory(target.hostname, target.port, timeout)
    try:
        connection.putrequest("PUT", request_target, skip_accept_encoding=True)
        connection.putheader("Content-Length", str(pdf_path.stat().st_size))
        connection.endheaders()
        with pdf_path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                connection.send(chunk)
        response = connection.getresponse()
        response.read(1024 * 1024)
        status = response.status
        if not isinstance(status, int) or not 200 <= status < 300:
            safe_status = status if isinstance(status, int) else "unknown"
            raise ExternalToolError(
                f"MinerU signed upload failed with HTTP {safe_status}."
            )
    except ExternalToolError:
        raise
    except (OSError, TimeoutError, http.client.HTTPException):
        raise ExternalToolError("MinerU signed upload failed; check network status.") from None
    finally:
        connection.close()


class MinerUApiParser:
    """Parse local PDFs through MinerU without persisting credentials."""

    name = "mineru_api"

    def __init__(
        self,
        opener: _Opener = _safe_urlopen,
        uploader: _Uploader = _upload_file,
        sleeper: _Sleeper = time.sleep,
        clock: _Clock = time.monotonic,
        max_poll_attempts: int = 120,
        poll_interval_seconds: float = 1.0,
        poll_timeout_seconds: float = _POLL_TIMEOUT_SECONDS,
    ) -> None:
        self._opener = opener
        self._uploader = uploader
        self._sleeper = sleeper
        self._clock = clock
        self._max_poll_attempts = max_poll_attempts
        self._poll_interval_seconds = poll_interval_seconds
        self._poll_timeout_seconds = poll_timeout_seconds

    def available(self) -> bool:
        return bool(os.environ.get("MINERU_API_KEY"))

    def parse(self, pdf_path: Path, workspace: Path) -> ParsedDocument:
        key = os.environ.get("MINERU_API_KEY")
        if not key:
            raise ExternalToolError("MinerU API is unavailable: MINERU_API_KEY is not set.")
        if not pdf_path.is_file():
            raise ExternalToolError("MinerU API input PDF does not exist.")

        request_payload = {
            "files": [{"name": pdf_path.name, "data_id": sha256_file(pdf_path)}],
            "model_version": "pipeline",
        }
        upload_response = self._request_json(
            Request(
                f"{_API_ROOT}/file-urls/batch",
                data=json.dumps(request_payload).encode("utf-8"),
                headers=self._api_headers(key),
                method="POST",
            )
        )
        upload_data = self._api_data(upload_response, "request upload URL")
        batch_id = upload_data.get("batch_id")
        file_urls = upload_data.get("file_urls")
        if not isinstance(batch_id, str) or not batch_id:
            raise ExternalToolError("MinerU API response is missing a batch ID.")
        if not isinstance(file_urls, list) or not file_urls:
            raise ExternalToolError("MinerU API response is missing an upload URL.")
        upload_url = file_urls[0]
        self._require_https_url(upload_url, "upload")

        self._uploader(upload_url, pdf_path, _HTTP_TIMEOUT_SECONDS)

        archive_url = self._poll_for_archive(batch_id, pdf_path.name, key)
        archive_bytes = self._request_bytes(
            Request(archive_url, method="GET"), max_bytes=_MAX_ARCHIVE_BYTES
        )

        raw_dir = workspace / "source" / "mineru-api"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "result.zip").write_bytes(archive_bytes)
        json_paths = self._extract_json(archive_bytes, raw_dir / "extracted")
        blocks = self._normalize_blocks(json_paths)
        if not blocks:
            raise ExternalToolError("MinerU result archive contains no usable JSON text.")
        return save_normalized_document(workspace, pdf_path, blocks)

    @staticmethod
    def _api_headers(key: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _api_data(payload: dict[str, Any], operation: str) -> dict[str, Any]:
        code = payload.get("code")
        if code != 0:
            safe_code = payload.get("msgCode", code if code is not None else "unknown")
            raise ExternalToolError(f"MinerU API could not {operation}; code {safe_code}.")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ExternalToolError(f"MinerU API could not {operation}; invalid response data.")
        return data

    @staticmethod
    def _require_https_url(value: object, purpose: str) -> str:
        if not isinstance(value, str) or not value.startswith("https://"):
            raise ExternalToolError(f"MinerU API returned an invalid {purpose} URL.")
        return value

    def _poll_for_archive(self, batch_id: str, file_name: str, key: str) -> str:
        poll_url = f"{_API_ROOT}/extract-results/batch/{batch_id}"
        deadline = self._clock() + self._poll_timeout_seconds
        for attempt in range(self._max_poll_attempts):
            remaining = deadline - self._clock()
            if remaining <= 0:
                break
            payload = self._request_json(
                Request(poll_url, headers=self._api_headers(key), method="GET"),
                timeout=min(_HTTP_TIMEOUT_SECONDS, remaining),
            )
            data = self._api_data(payload, "query extraction result")
            results = data.get("extract_result")
            if not isinstance(results, list) or not results:
                raise ExternalToolError("MinerU API result response contains no file status.")
            result = self._select_result(results, file_name)
            state = result.get("state")
            if state == "done":
                return self._require_https_url(result.get("full_zip_url"), "result")
            if state == "failed":
                error_code = self._safe_code(result.get("err_code"))
                error_message = self._safe_remote_message(result.get("err_msg"), key)
                code_text = f" with code {error_code}" if error_code != "unknown" else ""
                raise ExternalToolError(
                    f"MinerU extraction failed{code_text}: {error_message}."
                )
            if state not in {"waiting-file", "pending", "running", "converting"}:
                raise ExternalToolError(
                    f"MinerU API returned an unknown extraction state: {state!r}."
                )
            remaining = deadline - self._clock()
            if remaining <= 0:
                break
            if attempt + 1 < self._max_poll_attempts:
                self._sleeper(min(self._poll_interval_seconds, remaining))
        raise ExternalToolError(
            f"MinerU extraction timed out for batch {batch_id}."
        )

    @staticmethod
    def _select_result(results: list[Any], file_name: str) -> dict[str, Any]:
        valid = [result for result in results if isinstance(result, dict)]
        for result in valid:
            if result.get("file_name") == file_name:
                return result
        if valid:
            return valid[0]
        raise ExternalToolError("MinerU API result response contains no valid file status.")

    @staticmethod
    def _safe_code(value: object) -> str | int:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if (
            isinstance(value, str)
            and 0 < len(value) <= 32
            and all(character.isalnum() or character in "_-" for character in value)
        ):
            return value
        return "unknown"

    @staticmethod
    def _safe_remote_message(value: object, secret: str) -> str:
        if not isinstance(value, str):
            return "no error details provided"
        normalized = " ".join(value.split()).replace(secret, "[redacted]")
        return normalized[:200] or "no error details provided"

    def _request_json(
        self, request: Request, timeout: float = _HTTP_TIMEOUT_SECONDS
    ) -> dict[str, Any]:
        raw = self._request_bytes(
            request, timeout=timeout, max_bytes=_MAX_API_RESPONSE_BYTES
        )
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ExternalToolError("MinerU API returned an invalid JSON response.") from None
        if not isinstance(payload, dict):
            raise ExternalToolError("MinerU API returned an invalid JSON response.")
        return payload

    def _request_bytes(
        self,
        request: Request,
        timeout: float = _HTTP_TIMEOUT_SECONDS,
        max_bytes: int | None = None,
    ) -> bytes:
        try:
            with self._opener(request, timeout=timeout) as response:
                body = response.read(-1 if max_bytes is None else max_bytes + 1)
                if not isinstance(body, bytes):
                    raise ExternalToolError(
                        "MinerU API returned an invalid binary response."
                    )
                if max_bytes is not None and len(body) > max_bytes:
                    raise ExternalToolError("MinerU API response exceeds the size limit.")
                return body
        except HTTPError as exc:
            raise ExternalToolError(f"MinerU API request failed with HTTP {exc.code}.") from None
        except (URLError, OSError, TimeoutError):
            raise ExternalToolError(
                "MinerU API request failed; check network and API status."
            ) from None

    @staticmethod
    def _extract_json(archive_bytes: bytes, output_dir: Path) -> list[Path]:
        try:
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
                members = [
                    member
                    for member in archive.infolist()
                    if not member.is_dir() and member.filename.lower().endswith(".json")
                ]
                if not members:
                    raise ExternalToolError("MinerU result archive contains no JSON files.")
                if len(members) > _MAX_JSON_FILES:
                    raise ExternalToolError(
                        "MinerU result archive contains too many JSON files."
                    )
                total_size = sum(member.file_size for member in members)
                if total_size > _MAX_JSON_TOTAL_BYTES:
                    raise ExternalToolError(
                        "MinerU result archive JSON exceeds the size limit."
                    )
                for member in members:
                    if member.file_size > _MAX_JSON_MEMBER_BYTES:
                        raise ExternalToolError(
                            "MinerU result archive contains an oversized JSON file."
                        )
                    ratio = member.file_size / max(1, member.compress_size)
                    if ratio > _MAX_COMPRESSION_RATIO:
                        raise ExternalToolError(
                            "MinerU result archive has an unsafe compression ratio."
                        )
                output_dir.mkdir(parents=True, exist_ok=True)
                output_root = output_dir.resolve()
                extracted: list[Path] = []
                for member in members:
                    relative = PurePosixPath(member.filename)
                    if relative.is_absolute() or ".." in relative.parts:
                        raise ExternalToolError(
                            "MinerU result archive contains an unsafe JSON path."
                        )
                    destination = output_dir.joinpath(*relative.parts)
                    if not destination.resolve().is_relative_to(output_root):
                        raise ExternalToolError(
                            "MinerU result archive contains an unsafe JSON path."
                        )
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(member))
                    extracted.append(destination)
                return extracted
        except zipfile.BadZipFile:
            raise ExternalToolError("MinerU returned an invalid result archive.") from None

    @classmethod
    def _normalize_blocks(cls, json_paths: list[Path]) -> list[TextBlock]:
        preferred = [path for path in json_paths if "content_list" in path.name]
        sources = preferred or json_paths
        raw_blocks: list[tuple[int, str, tuple[float, float, float, float] | None]] = []
        for path in sorted(sources):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            raw_blocks.extend(cls._walk_text(payload, page_hint=1))

        blocks: list[TextBlock] = []
        for index, (page, text, bbox) in enumerate(raw_blocks):
            blocks.append(
                TextBlock(
                    id=f"p{page:02d}-b{index + 1:03d}",
                    page=page,
                    order=index,
                    text=text,
                    bbox=bbox,
                )
            )
        return blocks

    @classmethod
    def _walk_text(
        cls, value: Any, page_hint: int
    ) -> Iterator[tuple[int, str, tuple[float, float, float, float] | None]]:
        if isinstance(value, list):
            for child in value:
                yield from cls._walk_text(child, page_hint)
            return
        if not isinstance(value, dict):
            return

        page = cls._page_number(value, page_hint)
        text_value = value.get("text")
        if not isinstance(text_value, str):
            text_value = value.get("content")
        if isinstance(text_value, str) and text_value.strip():
            yield page, text_value.strip(), cls._bbox(value.get("bbox"))
            return

        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from cls._walk_text(child, page)

    @staticmethod
    def _page_number(value: dict[str, Any], default: int) -> int:
        page_idx = value.get("page_idx")
        if isinstance(page_idx, int) and not isinstance(page_idx, bool):
            return max(1, page_idx + 1)
        for key in ("page", "page_no", "page_number"):
            candidate = value.get(key)
            if isinstance(candidate, int) and not isinstance(candidate, bool):
                return max(1, candidate)
        return default

    @staticmethod
    def _bbox(value: object) -> tuple[float, float, float, float] | None:
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            return None
        if not all(isinstance(item, (int, float)) for item in value):
            return None
        return tuple(float(item) for item in value)  # type: ignore[return-value]


def save_normalized_document(
    workspace: Path, pdf_path: Path, blocks: list[TextBlock]
) -> ParsedDocument:
    """Persist a normalized document produced from a MinerU JSON result."""
    source_dir = workspace / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = source_dir / "parsed-paper.md"
    markdown_lines: list[str] = []
    last_page = 0
    for block in blocks:
        if block.page != last_page:
            markdown_lines.append(f"<!-- page:{block.page} -->\n")
            last_page = block.page
        markdown_lines.append(f"{block.text}\n<!-- {block.id} -->")
    markdown_path.write_text("\n\n".join(markdown_lines), encoding="utf-8")
    document = ParsedDocument(
        parser_name="mineru_api",
        pdf_sha256=sha256_file(pdf_path),
        title_guess=blocks[0].text if blocks else None,
        page_count=max((block.page for block in blocks), default=1),
        markdown_path=str(markdown_path),
        blocks=blocks,
    )
    write_json(source_dir / "parsed-document.json", document.model_dump(mode="json"))
    return document
