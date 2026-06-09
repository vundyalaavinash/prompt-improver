import subprocess
import pytest
from unittest.mock import MagicMock, patch
from src.claude_adapter import ClaudeAdapter


def _mock_run(stdout: str, returncode: int = 0) -> MagicMock:
    mock = MagicMock()
    mock.stdout = stdout
    mock.stderr = ""
    mock.returncode = returncode
    return mock


def test_call_returns_text():
    with patch("src.claude_adapter.subprocess.run", return_value=_mock_run("hello")):
        adapter = ClaudeAdapter()
        result = adapter.call(system="You are helpful.", user="Say hello.")
    assert result == "hello"


def test_call_structured_parses_json():
    text = 'Some text {"clarity": 80, "specificity": 70, "hallucination_resistance": 60} more text'
    with patch("src.claude_adapter.subprocess.run", return_value=_mock_run(text)):
        adapter = ClaudeAdapter()
        result = adapter.call_structured(
            system="Score this.",
            user="Prompt here.",
            schema={"type": "object"},
        )
    assert result["clarity"] == 80
    assert result["specificity"] == 70


def test_call_structured_raises_on_no_json():
    with patch("src.claude_adapter.subprocess.run", return_value=_mock_run("no json here")):
        adapter = ClaudeAdapter()
        with pytest.raises(ValueError, match="No JSON found"):
            adapter.call_structured(system="s", user="u", schema={})


def test_call_raises_on_nonzero_exit():
    with patch("src.claude_adapter.subprocess.run", return_value=_mock_run("", returncode=1)):
        adapter = ClaudeAdapter()
        with pytest.raises(RuntimeError, match="claude CLI error"):
            adapter.call(system="s", user="u")
