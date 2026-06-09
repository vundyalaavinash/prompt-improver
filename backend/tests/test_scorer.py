import pytest
from src.scorer import Scorer
from src.llm_adapter import LLMAdapter


class MockAdapter(LLMAdapter):
    def call(self, system: str, user: str) -> str:
        return '{"clarity": 70, "specificity": 60, "hallucination_resistance": 50}'

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        return {"clarity": 70, "specificity": 60, "hallucination_resistance": 50}


def test_score_returns_all_dimensions():
    scorer = Scorer(MockAdapter())
    result = scorer.score("Summarize this document.")
    assert set(result.keys()) >= {
        "token_efficiency",
        "format_control",
        "clarity",
        "specificity",
        "hallucination_resistance",
        "overall",
    }


def test_token_efficiency_penalizes_long_prompts():
    scorer = Scorer(MockAdapter())
    short = scorer.score("Summarize.")
    long = scorer.score(
        "Please provide a very comprehensive and detailed summary of the following "
        "long document, making sure to include all key points and nuances in your response. "
        "Be thorough and exhaustive in your coverage of all topics discussed."
    )
    assert short["token_efficiency"] > long["token_efficiency"]


def test_format_control_detects_json_instruction():
    scorer = Scorer(MockAdapter())
    with_format = scorer.score("Extract the names. Return JSON.")
    without_format = scorer.score("Extract the names.")
    assert with_format["format_control"] > without_format["format_control"]


def test_overall_is_average_of_five():
    scorer = Scorer(MockAdapter())
    result = scorer.score("Tell me about Python.")
    expected = int(
        (
            result["token_efficiency"]
            + result["format_control"]
            + result["clarity"]
            + result["specificity"]
            + result["hallucination_resistance"]
        )
        / 5
    )
    assert result["overall"] == expected


def test_scores_are_bounded_0_to_100():
    scorer = Scorer(MockAdapter())
    result = scorer.score("A" * 3000)
    for key, value in result.items():
        assert 0 <= value <= 100, f"{key} out of range: {value}"
