import pytest
import httpx
from unittest.mock import MagicMock, patch
from src.ollama_adapter import OllamaAdapter


def test_call_returns_text():
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "hello from ollama"}}
    mock_response.raise_for_status = MagicMock()

    with patch("src.ollama_adapter.httpx.post", return_value=mock_response):
        adapter = OllamaAdapter()
        result = adapter.call(system="You are helpful.", user="Say hello.")

    assert result == "hello from ollama"


def test_call_structured_parses_json():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {
            "content": '{"clarity": 75, "specificity": 65, "hallucination_resistance": 55}'
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("src.ollama_adapter.httpx.post", return_value=mock_response):
        adapter = OllamaAdapter()
        result = adapter.call_structured(system="Score this.", user="Prompt.", schema={})

    assert result["clarity"] == 75


def test_call_raises_on_connection_error():
    with patch(
        "src.ollama_adapter.httpx.post",
        side_effect=httpx.ConnectError("refused"),
    ):
        adapter = OllamaAdapter()
        with pytest.raises(httpx.ConnectError):
            adapter.call(system="s", user="u")
