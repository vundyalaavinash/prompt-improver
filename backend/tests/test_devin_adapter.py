import pytest
from unittest.mock import MagicMock, patch
from src.devin_adapter import DevinAdapter


def _mock_run(stdout: str, returncode: int = 0) -> MagicMock:
    mock = MagicMock()
    mock.stdout = stdout
    mock.stderr = ""
    mock.returncode = returncode
    return mock


def _mock_http(content: str) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = {"choices": [{"message": {"content": content}}]}
    mock.raise_for_status = MagicMock()
    return mock


# ── CLI mode ────────────────────────────────────────────────────────────────

def test_cli_call_returns_text():
    with patch("src.devin_adapter.shutil.which", return_value="/usr/bin/devin"), \
         patch("src.devin_adapter.subprocess.run", return_value=_mock_run("cli response")):
        adapter = DevinAdapter()
        result = adapter.call(system="You are helpful.", user="Hi.")
    assert result == "cli response"


def test_cli_call_raises_on_nonzero_exit():
    with patch("src.devin_adapter.shutil.which", return_value="/usr/bin/devin"), \
         patch("src.devin_adapter.subprocess.run", return_value=_mock_run("", returncode=1)):
        adapter = DevinAdapter()
        with pytest.raises(RuntimeError, match="devin CLI error"):
            adapter.call(system="s", user="u")


# ── API mode ─────────────────────────────────────────────────────────────────

def test_api_call_returns_text():
    with patch("src.devin_adapter.shutil.which", return_value=None), \
         patch("src.devin_adapter.httpx.post", return_value=_mock_http("api response")):
        adapter = DevinAdapter(api_key="tok-123")
        result = adapter.call(system="You are helpful.", user="Hi.")
    assert result == "api response"


def test_api_call_structured_parses_json():
    text = '{"clarity": 80, "specificity": 70, "hallucination_resistance": 60}'
    with patch("src.devin_adapter.shutil.which", return_value=None), \
         patch("src.devin_adapter.httpx.post", return_value=_mock_http(text)):
        adapter = DevinAdapter(api_key="tok-123")
        result = adapter.call_structured(system="Score.", user="Prompt.", schema={})
    assert result["clarity"] == 80


# ── neither available ────────────────────────────────────────────────────────

def test_raises_when_neither_cli_nor_key():
    with patch("src.devin_adapter.shutil.which", return_value=None):
        adapter = DevinAdapter(api_key="")
        with pytest.raises(RuntimeError, match="not available"):
            adapter.call(system="s", user="u")
