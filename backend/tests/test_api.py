from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def _make_mock_engine():
    from src.gepa_engine import Candidate, GenerationEvent

    gen0 = GenerationEvent(
        generation=0,
        candidate=Candidate(
            prompt="original",
            scores={
                "token_efficiency": 50,
                "format_control": 0,
                "clarity": 60,
                "specificity": 50,
                "hallucination_resistance": 40,
                "overall": 40,
            },
        ),
        reflection="Original prompt scored.",
        event_type="generation",
    )
    done = GenerationEvent(
        generation=2,
        candidate=Candidate(
            prompt="improved prompt text",
            scores={
                "token_efficiency": 80,
                "format_control": 50,
                "clarity": 80,
                "specificity": 80,
                "hallucination_resistance": 70,
                "overall": 72,
            },
        ),
        reflection="Evolution complete.",
        event_type="done",
    )
    mock = MagicMock()
    mock.run.return_value = iter([gen0, done])
    mock.top_candidates.return_value = [done.candidate]
    return mock


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_improve_returns_sse_stream():
    with (
        patch("src.main.GEPAEngine", return_value=_make_mock_engine()),
        patch("src.main.get_adapter", return_value=MagicMock()),
        patch("src.main.Scorer", return_value=MagicMock()),
    ):
        response = client.post(
            "/api/improve",
            json={"prompt": "Tell me about Python.", "depth": "quick", "backend": "claude"},
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    events = [l for l in response.text.split("\n") if l.startswith("data: ")]
    assert len(events) >= 2


def test_improve_rejects_empty_prompt():
    response = client.post(
        "/api/improve",
        json={"prompt": "", "depth": "quick", "backend": "claude"},
    )
    assert response.status_code == 422
