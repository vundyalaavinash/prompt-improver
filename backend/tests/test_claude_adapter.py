import pytest
from unittest.mock import MagicMock, patch
from src.claude_adapter import ClaudeAdapter


def _mock_response(text: str) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = {"content": [{"text": text}]}
    mock.raise_for_status = MagicMock()
    return mock


def test_call_returns_text():
    with patch("src.claude_adapter.httpx.post", return_value=_mock_response("hello")):
        adapter = ClaudeAdapter(api_key="test-key")
        result = adapter.call(system="You are helpful.", user="Say hello.")

    assert result == "hello"


def test_call_structured_parses_json():
    text = 'Some text {"clarity": 80, "specificity": 70, "hallucination_resistance": 60} more text'
    with patch("src.claude_adapter.httpx.post", return_value=_mock_response(text)):
        adapter = ClaudeAdapter(api_key="test-key")
        result = adapter.call_structured(
            system="Score this.",
            user="Prompt here.",
            schema={"type": "object"},
        )

    assert result["clarity"] == 80
    assert result["specificity"] == 70


def test_call_structured_raises_on_no_json():
    with patch("src.claude_adapter.httpx.post", return_value=_mock_response("no json here")):
        adapter = ClaudeAdapter(api_key="test-key")
        with pytest.raises(ValueError, match="No JSON found"):
            adapter.call_structured(system="s", user="u", schema={})
