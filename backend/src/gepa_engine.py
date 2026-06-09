import json
from dataclasses import dataclass
from typing import Generator

from .llm_adapter import LLMAdapter
from .scorer import Scorer

REFLECT_SYSTEM = (
    "You are a prompt optimization expert. Analyze the given prompt and its dimension scores, "
    "then explain specifically what weaknesses need to be fixed. Be concrete: name the exact phrases, "
    "missing elements, or structural problems. Keep your reflection under 100 words."
)

MUTATE_SYSTEM = (
    "You are a prompt rewriting expert. Rewrite the given prompt to fix the identified weaknesses. Rules:\n"
    "- Make it more specific and unambiguous\n"
    "- Remove filler words and redundancy\n"
    "- Add output format instructions if missing\n"
    "- Add grounding instructions if missing (e.g. 'Only use provided information', 'If unsure, say so')\n"
    "- Keep the core intent identical\n"
    "Return ONLY the rewritten prompt, nothing else."
)


@dataclass
class Candidate:
    prompt: str
    scores: dict
    reflection: str = ""
    generation: int = 0


@dataclass
class GenerationEvent:
    generation: int
    candidate: Candidate
    reflection: str
    event_type: str = "generation"


class GEPAEngine:
    def __init__(self, adapter: LLMAdapter, scorer: Scorer, generations: int = 2):
        self.adapter = adapter
        self.scorer = scorer
        self.generations = generations
        self.pareto_front: list[Candidate] = []

    def run(self, prompt: str) -> Generator[GenerationEvent, None, None]:
        initial_scores = self.scorer.score(prompt)
        initial = Candidate(prompt=prompt, scores=initial_scores, generation=0)
        self.pareto_front = [initial]
        yield GenerationEvent(
            generation=0,
            candidate=initial,
            reflection="Original prompt scored.",
            event_type="generation",
        )

        for gen in range(1, self.generations + 1):
            candidate = min(self.pareto_front, key=lambda c: c.scores["overall"])

            reflection = self.adapter.call(
                REFLECT_SYSTEM,
                f"Prompt:\n{candidate.prompt}\n\nScores:\n{json.dumps(candidate.scores, indent=2)}",
            )

            improved_prompt = self.adapter.call(
                MUTATE_SYSTEM,
                f"Original prompt:\n{candidate.prompt}\n\nWeaknesses:\n{reflection}",
            )

            new_scores = self.scorer.score(improved_prompt)
            new_candidate = Candidate(
                prompt=improved_prompt,
                scores=new_scores,
                reflection=reflection,
                generation=gen,
            )

            if new_scores["overall"] > candidate.scores["overall"]:
                self.pareto_front.append(new_candidate)

            yield GenerationEvent(
                generation=gen,
                candidate=new_candidate,
                reflection=reflection,
                event_type="generation",
            )

        yield GenerationEvent(
            generation=self.generations,
            candidate=self._best_candidate(),
            reflection="Evolution complete.",
            event_type="done",
        )

    def _best_candidate(self) -> Candidate:
        return max(self.pareto_front, key=lambda c: c.scores["overall"])

    def top_candidates(self, n: int = 3) -> list[Candidate]:
        return sorted(self.pareto_front, key=lambda c: c.scores["overall"], reverse=True)[:n]
