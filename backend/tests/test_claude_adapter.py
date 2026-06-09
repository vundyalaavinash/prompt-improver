import pytest
from unittest.mock import MagicMock, patch
from src.claude_adapter import ClaudeAdapter


def test_call_returns_text():
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text="hello")]

    with patch("src.claude_adapter.anthropic.Anthropic", return_value=mock_client):
        adapter = ClaudeAdapter(api_key="test-key")
        result = adapter.call(system="You are helpful.", user="Say hello.")

    assert result == "hello"
    mock_client.messages.create.assert_called_once()


def test_call_structured_parses_json():
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [
        MagicMock(
            text='Some text {"clarity": 80, "specificity": 70, "hallucination_resistance": 60} more text'
        )
    ]

    with patch("src.claude_adapter.anthropic.Anthropic", return_value=mock_client):
        adapter = ClaudeAdapter(api_key="test-key")
        result = adapter.call_structured(
            system="Score this.",
            user="Prompt here.",
            schema={"type": "object"},
        )

    assert result["clarity"] == 80
    assert result["specificity"] == 70


def test_call_structured_raises_on_no_json():
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content = [MagicMock(text="no json here")]

    with patch("src.claude_adapter.anthropic.Anthropic", return_value=mock_client):
        adapter = ClaudeAdapter(api_key="test-key")
        with pytest.raises(ValueError, match="No JSON found"):
            adapter.call_structured(system="s", user="u", schema={})
