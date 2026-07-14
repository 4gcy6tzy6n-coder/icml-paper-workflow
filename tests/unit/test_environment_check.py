import pytest

from paperflow.util.check_environment import check_environment


def test_environment_check_returns_all_tools() -> None:
    checks = check_environment()
    names = {c.name for c in checks}
    required_tools = {
        "Python", "uv", "Node.js", "pnpm",
        "PyMuPDF", "Quarto", "LibreOffice", "Poppler",
    }
    for tool in required_tools:
        assert tool in names, f"Missing tool check: {tool}"


def test_python_is_always_available() -> None:
    checks = check_environment()
    python = next(c for c in checks if c.name == "Python")
    assert python.available is True
    assert python.version is not None


def test_optional_tools_are_not_required() -> None:
    checks = check_environment()
    mineru = next(c for c in checks if c.name == "MinerU")
    markitdown = next(c for c in checks if c.name == "MarkItDown")
    assert mineru.required is False
    assert markitdown.required is False


def test_mineru_api_status_uses_environment_without_exposing_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MINERU_API_KEY", "test-secret-value")

    checks = check_environment()

    mineru_api = next(check for check in checks if check.name == "MinerU API")
    assert mineru_api.available is True
    assert mineru_api.required is False
    assert "test-secret-value" not in repr(checks)
