import json
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from .claude_adapter import ClaudeAdapter
from .config import get_config
from .gepa_engine import GEPAEngine
from .llm_adapter import LLMAdapter
from .ollama_adapter import OllamaAdapter
from .scorer import Scorer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ImproveRequest(BaseModel):
    prompt: str
    depth: Literal["quick", "thorough"] = "quick"
    target_model: str = "generic"
    backend: Literal["claude", "ollama"] = "claude"

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("prompt must not be empty")
        return v


def get_adapter(backend: str, config, target_model: str = "generic") -> LLMAdapter:
    if backend == "claude":
        model = target_model if target_model and target_model != "generic" else config.claude_model
        return ClaudeAdapter(model=model)
    model = target_model if target_model and target_model != "generic" else config.ollama_model
    return OllamaAdapter(base_url=config.ollama_base_url, model=model)


@app.post("/api/improve")
async def improve_prompt(request: ImproveRequest):
    config = get_config()
    generations = 2 if request.depth == "quick" else 5

    def generate():
        engine = None
        try:
            adapter = get_adapter(request.backend, config, request.target_model)
            scorer = Scorer(adapter)
            engine = GEPAEngine(adapter=adapter, scorer=scorer, generations=generations)

            for event in engine.run(request.prompt):
                data: dict = {
                    "type": event.event_type,
                    "generation": event.generation,
                    "prompt": event.candidate.prompt,
                    "scores": event.candidate.scores,
                    "reflection": event.reflection,
                }
                if event.event_type == "done":
                    data["top_candidates"] = [
                        {
                            "prompt": c.prompt,
                            "scores": c.scores,
                            "reflection": c.reflection,
                            "generation": c.generation,
                        }
                        for c in engine.top_candidates(3)
                    ]
                yield f"data: {json.dumps(data)}\n\n"
        except Exception as e:
            error_data: dict = {"type": "error", "message": str(e)}
            if engine is not None and engine.pareto_front:
                try:
                    error_data["top_candidates"] = [
                        {
                            "prompt": c.prompt,
                            "scores": c.scores,
                            "reflection": c.reflection,
                            "generation": c.generation,
                        }
                        for c in engine.top_candidates(3)
                    ]
                except Exception:
                    pass
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
