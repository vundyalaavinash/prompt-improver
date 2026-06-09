# Prompt Improver — Design Spec

**Date:** 2026-06-09
**Status:** Approved

---

## Overview

A web application for developers that takes any prompt and returns an improved version that is token-efficient, clearly specified, hallucination-resistant, and format-controlled. Improvement is powered by a GEPA (Genetic-Pareto) evolutionary loop that iteratively reflects on weaknesses and mutates the prompt over multiple generations. The LLM backend is configurable between Claude API and Ollama (local).

---

## Goals

- Improve prompts across 5 dimensions: token efficiency, clarity, specificity, hallucination resistance, format control
- Show before/after scores per dimension, what changed, and the reasoning behind each change
- Support Claude and Ollama as LLM backends, switchable via config
- Allow an optional target model field (defaults to "generic" if not specified)
- Stream evolution progress in real-time so the user sees improvement happening live

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Browser (React)                │
│  ┌──────────┐  ┌────────────┐  ┌─────────┐ │
│  │  Input   │  │ Evolution  │  │ Results │ │
│  │  Panel   │  │  Viewer    │  │  Panel  │ │
│  └──────────┘  └────────────┘  └─────────┘ │
└─────────────────────────┬───────────────────┘
                          │ HTTP / SSE
┌─────────────────────────▼───────────────────┐
│              FastAPI Backend                │
│  ┌──────────────────────────────────────┐   │
│  │           GEPA Engine                │   │
│  │   Scorer → Reflector → Mutator       │   │
│  │   (Pareto frontier maintained here)  │   │
│  └──────────────────────────────────────┘   │
│  ┌──────────────────────────────────────┐   │
│  │         LLM Adapter Layer            │   │
│  │       ClaudeAdapter | OllamaAdapter  │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

- **Frontend:** React + TypeScript. Streams generation events via Server-Sent Events (SSE).
- **Backend:** Python FastAPI. Stateless per-request; GEPA evolution state lives in memory for the duration of one run.
- **No database.** No auth. Designed to run locally or on a private server.

---

## Components

### Frontend

| Component | Responsibility |
|---|---|
| **Input Panel** | Prompt textarea, target model field (optional), depth selector (quick=2 gens / thorough=5 gens), backend selector (Claude / Ollama) |
| **Evolution Viewer** | Live stream of each generation: gen number, dimension scores, LLM reflection, mutation applied |
| **Results Panel** | Top-3 Pareto-optimal candidates with before/after scores, diff view, copy button |

Diff is computed client-side using the `diff` npm package — no extra LLM call.

### Backend

| Unit | Responsibility |
|---|---|
| **`POST /api/improve`** | Accepts prompt + config, streams SSE events, returns top-3 candidates on completion |
| **`GEPAEngine`** | Orchestrates the Select → Score → Reflect → Mutate → Accept loop for N generations |
| **`Scorer`** | Scores a prompt across 5 dimensions (see Scoring section below) |
| **`LLMAdapter`** | Common interface; `ClaudeAdapter` and `OllamaAdapter` are the two concrete implementations |

---

## GEPA Evolution Loop

```
User submits prompt + config
        │
        ▼
POST /api/improve  →  stream SSE events
        │
        ▼
GEPAEngine.run(prompt, config)
        │
        ├─ Generation 0: score original prompt
        │   └─ Scorer.score(original_prompt)
        │       → {token_efficiency: 40, clarity: 35, specificity: 50, ...}
        │
        ├─ Generation 1..N:
        │   ├─ Select: pick weakest candidate on Pareto front
        │   ├─ Reflect: LLMAdapter.call(reflect_prompt + scores + prompt)
        │   │   → "Prompt is vague on output format, uses 3 filler phrases"
        │   ├─ Mutate: LLMAdapter.call(mutate_prompt + reflection + prompt)
        │   │   → improved_prompt_candidate
        │   ├─ Score: Scorer.score(improved_prompt_candidate)
        │   └─ Accept: update Pareto front if improved
        │       → emit SSE event {gen, scores, reflection, diff}
        │
        └─ Final: return top-3 Pareto candidates
                → emit SSE event {type: "done", results: [...]}
```

**Generation depth:**
- Quick: 2 generations (~4 LLM calls total)
- Thorough: 5 generations (~10 LLM calls total)

---

## Scoring

### Heuristic (no LLM cost)

| Dimension | Method |
|---|---|
| **Token efficiency** | Character count + estimated token count via `tiktoken` |
| **Format control** | Regex check for presence of output format instruction (e.g., "return JSON", "bullet list") |

### LLM-scored (1 batched call per generation)

| Dimension | Scored via |
|---|---|
| **Clarity** | Single structured LLM call returning scores 0–100 for all 3 dimensions at once |
| **Specificity** | (same call) |
| **Hallucination resistance** | (same call) — checks for grounding instructions, uncertainty acknowledgment, scope constraints |

Scores are always 0–100. Batching the 3 LLM-scored dimensions into one call keeps per-generation cost to 3 LLM calls: 1 score call, 1 reflect call, 1 mutate call.

---

## LLM Adapter

Common interface:
```python
class LLMAdapter:
    def call(self, system: str, user: str) -> str: ...
    def call_structured(self, system: str, user: str, schema: dict) -> dict: ...
```

| Adapter | Backend | Config |
|---|---|---|
| `ClaudeAdapter` | Anthropic Claude API | `CLAUDE_API_KEY`, `CLAUDE_MODEL` (default: `claude-sonnet-4-6`) |
| `OllamaAdapter` | Local Ollama HTTP API | `OLLAMA_BASE_URL` (default: `http://localhost:11434`), `OLLAMA_MODEL` (default: `llama3.2`) |

### `.env` configuration

```
BACKEND=claude          # claude | ollama
CLAUDE_API_KEY=sk-...
CLAUDE_MODEL=claude-sonnet-4-6
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| LLM call fails mid-generation | Emit SSE error event, stop loop, return Pareto candidates collected so far |
| LLM returns malformed structured output | Retry up to 2 times with exponential backoff; if still failing, skip that generation |
| Ollama not running | Return clear error: "Ollama is not reachable at `{OLLAMA_BASE_URL}`" |
| Empty prompt submitted | Frontend validation — block submission before API call |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Styling | Tailwind CSS |
| Diff view | `diff` npm package |
| Backend | Python 3.11+, FastAPI |
| LLM — Claude | `anthropic` Python SDK |
| LLM — Ollama | `httpx` (direct HTTP to Ollama API) |
| Token counting | `tiktoken` |
| Streaming | Server-Sent Events (SSE) |

---

## Out of Scope (v1)

- OpenAI / custom LLM backends (architecture supports it; implementation deferred)
- Prompt history / saving past improvements
- User accounts or auth
- Batch processing multiple prompts at once
- Fine-tuned evaluation models for scoring
