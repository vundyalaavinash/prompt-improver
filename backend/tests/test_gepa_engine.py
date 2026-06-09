import pytest
from src.gepa_engine import GEPAEngine, Candidate
from src.llm_adapter import LLMAdapter


class MockAdapter(LLMAdapter):
    def call(self, system: str, user: str) -> str:
        if "rewriting expert" in system.lower():
            return "improved: be specific, return JSON, only use provided data"
        return "needs clearer output format"

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        return {"clarity": 70, "specificity": 60, "hallucination_resistance": 50}


class MockScorer:
    def __init__(self, scores: dict | None = None):
        self._scores = scores or {
            "token_efficiency": 80,
            "format_control": 50,
            "clarity": 70,
            "specificity": 60,
            "hallucination_resistance": 50,
            "overall": 62,
        }

    def score(self, prompt: str) -> dict:
        return self._scores.copy()


def test_run_yields_generation_0_first():
    engine = GEPAEngine(adapter=MockAdapter(), scorer=MockScorer(), generations=1)
    events = list(engine.run("Write a summary."))
    assert events[0].generation == 0
    assert events[0].event_type == "generation"


def test_run_yields_correct_event_count():
    engine = GEPAEngine(adapter=MockAdapter(), scorer=MockScorer(), generations=2)
    events = list(engine.run("Write a summary."))
    # gen 0 + gen 1 + gen 2 + done = 4
    assert len(events) == 4
    assert events[-1].event_type == "done"


def test_top_candidates_returns_at_most_n():
    engine = GEPAEngine(adapter=MockAdapter(), scorer=MockScorer(), generations=3)
    list(engine.run("Write a summary."))
    assert len(engine.top_candidates(3)) <= 3


def test_pareto_front_grows_when_improved():
    low = {"token_efficiency": 30, "format_control": 20, "clarity": 30, "specificity": 30, "hallucination_resistance": 30, "overall": 28}
    high = {"token_efficiency": 90, "format_control": 90, "clarity": 90, "specificity": 90, "hallucination_resistance": 90, "overall": 90}

    call_count = [0]

    class ProgressingScorer:
        def score(self, prompt: str) -> dict:
            call_count[0] += 1
            return high.copy() if call_count[0] > 1 else low.copy()

    engine = GEPAEngine(adapter=MockAdapter(), scorer=ProgressingScorer(), generations=1)
    list(engine.run("original"))
    assert len(engine.pareto_front) == 2
