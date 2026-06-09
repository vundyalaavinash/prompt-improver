# Prompt Improver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web app that takes a prompt and returns GEPA-evolved, token-efficient, hallucination-resistant improved versions with before/after scores and a diff view, supporting Claude and Ollama as configurable backends.

**Architecture:** FastAPI backend runs the GEPA loop (Select → Score → Reflect → Mutate → Accept), streaming SSE events to a React frontend. Two LLM backends — Claude API and Ollama — are configured via `.env` and switchable per-request.

**Tech Stack:** Python 3.11+, FastAPI, anthropic SDK, httpx, tiktoken, pytest | React 18, TypeScript, Vite, Tailwind CSS, diff npm package

---

## File Map

### Backend (`backend/`)

| File | Responsibility |
|---|---|
| `src/config.py` | Load env vars into a Config object |
| `src/llm_adapter.py` | Abstract base class + retry helper for LLM adapters |
| `src/claude_adapter.py` | ClaudeAdapter: wraps anthropic SDK |
| `src/ollama_adapter.py` | OllamaAdapter: wraps Ollama HTTP API via httpx |
| `src/scorer.py` | Scorer: heuristic + LLM dimension scoring (0–100 per dimension) |
| `src/gepa_engine.py` | GEPAEngine: orchestrates Select→Score→Reflect→Mutate→Accept loop |
| `src/main.py` | FastAPI app, CORS, `/api/improve` SSE endpoint, `/api/health` |
| `tests/test_claude_adapter.py` | Unit tests for ClaudeAdapter |
| `tests/test_ollama_adapter.py` | Unit tests for OllamaAdapter |
| `tests/test_scorer.py` | Unit tests for Scorer |
| `tests/test_gepa_engine.py` | Unit tests for GEPAEngine |
| `tests/test_api.py` | Integration tests for /api/improve endpoint |

### Frontend (`frontend/`)

| File | Responsibility |
|---|---|
| `src/types.ts` | Shared TypeScript interfaces (Scores, Candidate, GenerationEvent, ImproveConfig) |
| `src/hooks/useImprove.ts` | SSE connection management and state |
| `src/components/ScoreBar.tsx` | Reusable score bar with label, value, delta |
| `src/components/InputPanel.tsx` | Prompt textarea, backend/depth/target-model config, submit |
| `src/components/EvolutionViewer.tsx` | Live stream of generation events with per-generation scores |
| `src/components/ResultsPanel.tsx` | Top-3 candidates with diff view and copy button |
| `src/App.tsx` | Root layout, wires all components together |

---

## Task 1: Project scaffolding

**Files:**
- Create: `backend/src/__init__.py`, `backend/tests/__init__.py`
- Create: `backend/requirements.txt`, `backend/pyproject.toml`, `backend/.env.example`
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tailwind.config.js`
- Create: `frontend/tsconfig.json`, `frontend/postcss.config.js`, `frontend/index.html`
- Create: `frontend/src/main.tsx`, `frontend/src/index.css`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p backend/src backend/tests frontend/src/components frontend/src/hooks
touch backend/src/__init__.py backend/tests/__init__.py
```

- [ ] **Step 2: Create `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
anthropic==0.40.0
httpx==0.27.2
tiktoken==0.8.0
pydantic==2.9.2
pydantic-settings==2.6.1
pytest==8.3.3
pytest-asyncio==0.24.0
python-dotenv==1.0.1
```

- [ ] **Step 3: Create `backend/pyproject.toml`**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: Create `backend/.env.example`**

```
BACKEND=claude
CLAUDE_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-6
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

- [ ] **Step 5: Install backend dependencies**

```bash
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

Expected: All packages install without error.

- [ ] **Step 6: Create `frontend/package.json`**

```json
{
  "name": "prompt-improver",
  "version": "0.1.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "diff": "^5.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@types/diff": "^5.2.3",
    "@vitejs/plugin-react": "^4.3.3",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.3",
    "vite": "^5.4.10"
  }
}
```

- [ ] **Step 7: Create `frontend/vite.config.ts`**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

- [ ] **Step 8: Create `frontend/tailwind.config.js`**

```javascript
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

- [ ] **Step 9: Create `frontend/postcss.config.js`**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 10: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
```

- [ ] **Step 11: Create `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Prompt Improver</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 12: Create `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 13: Create `frontend/src/main.tsx`**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 14: Install frontend dependencies**

```bash
cd frontend && npm install
```

Expected: `node_modules` created, no errors.

- [ ] **Step 15: Commit**

```bash
git init
git add backend/ frontend/
git commit -m "feat: scaffold backend and frontend project structure"
```

---

## Task 2: Config module

**Files:**
- Create: `backend/src/config.py`

- [ ] **Step 1: Write `backend/src/config.py`**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    backend: str = "claude"
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_config() -> Config:
    return Config()
```

- [ ] **Step 2: Verify config loads without a .env file**

```bash
cd backend && source .venv/bin/activate && python -c "from src.config import get_config; c = get_config(); print(c.claude_model)"
```

Expected: `claude-sonnet-4-6`

- [ ] **Step 3: Commit**

```bash
git add backend/src/config.py
git commit -m "feat: add config module with pydantic-settings"
```

---

## Task 3: LLM Adapter base class with retry

**Files:**
- Create: `backend/src/llm_adapter.py`

- [ ] **Step 1: Write `backend/src/llm_adapter.py`**

```python
import time
from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    @abstractmethod
    def call(self, system: str, user: str) -> str:
        """Send a chat request and return the text response."""

    @abstractmethod
    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        """Send a chat request expecting JSON output matching schema."""

    def call_structured_with_retry(
        self, system: str, user: str, schema: dict, retries: int = 2
    ) -> dict:
        last_error: Exception = RuntimeError("No attempts made")
        for attempt in range(retries + 1):
            try:
                return self.call_structured(system, user, schema)
            except (ValueError, Exception) as e:
                last_error = e
                if attempt < retries:
                    time.sleep(2**attempt)  # 1s then 2s
        raise last_error
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/llm_adapter.py
git commit -m "feat: add LLMAdapter base class with retry helper"
```

---

## Task 4: ClaudeAdapter

**Files:**
- Create: `backend/src/claude_adapter.py`
- Test: `backend/tests/test_claude_adapter.py`

- [ ] **Step 1: Write the failing test `backend/tests/test_claude_adapter.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_claude_adapter.py -v
```

Expected: `ImportError: cannot import name 'ClaudeAdapter'`

- [ ] **Step 3: Write `backend/src/claude_adapter.py`**

```python
import json
import re

import anthropic

from .llm_adapter import LLMAdapter


class ClaudeAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def call(self, system: str, user: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        system_with_json = (
            system
            + "\n\nRespond ONLY with valid JSON matching this schema: "
            + json.dumps(schema)
        )
        response = self.call(system_with_json, user)
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {response}")
        return json.loads(match.group())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_claude_adapter.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/claude_adapter.py backend/tests/test_claude_adapter.py
git commit -m "feat: add ClaudeAdapter with tests"
```

---

## Task 5: OllamaAdapter

**Files:**
- Create: `backend/src/ollama_adapter.py`
- Test: `backend/tests/test_ollama_adapter.py`

- [ ] **Step 1: Write the failing test `backend/tests/test_ollama_adapter.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_ollama_adapter.py -v
```

Expected: `ImportError: cannot import name 'OllamaAdapter'`

- [ ] **Step 3: Write `backend/src/ollama_adapter.py`**

```python
import json
import re

import httpx

from .llm_adapter import LLMAdapter


class OllamaAdapter(LLMAdapter):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def call(self, system: str, user: str) -> str:
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def call_structured(self, system: str, user: str, schema: dict) -> dict:
        system_with_json = (
            system
            + "\n\nRespond ONLY with valid JSON matching this schema: "
            + json.dumps(schema)
        )
        response = self.call(system_with_json, user)
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {response}")
        return json.loads(match.group())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_ollama_adapter.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/ollama_adapter.py backend/tests/test_ollama_adapter.py
git commit -m "feat: add OllamaAdapter with tests"
```

---

## Task 6: Scorer

**Files:**
- Create: `backend/src/scorer.py`
- Test: `backend/tests/test_scorer.py`

- [ ] **Step 1: Write the failing test `backend/tests/test_scorer.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_scorer.py -v
```

Expected: `ImportError: cannot import name 'Scorer'`

- [ ] **Step 3: Write `backend/src/scorer.py`**

```python
import re

import tiktoken

from .llm_adapter import LLMAdapter

FORMAT_PATTERNS = [
    r"\bjson\b",
    r"\bmarkdown\b",
    r"\bbullets?\b",
    r"\bbullet list\b",
    r"\bnumbered list\b",
    r"\bformat:\b",
    r"\bstructured as\b",
    r"\bin the format\b",
    r"\boutput as\b",
    r"\breturn (?:a |an )?(?:list|json|dict|array)\b",
    r"\bplain text\b",
    r"\bcsv\b",
    r"\bxml\b",
]

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "clarity": {"type": "integer", "minimum": 0, "maximum": 100},
        "specificity": {"type": "integer", "minimum": 0, "maximum": 100},
        "hallucination_resistance": {"type": "integer", "minimum": 0, "maximum": 100},
    },
    "required": ["clarity", "specificity", "hallucination_resistance"],
}

SCORE_SYSTEM = (
    "You are an expert prompt evaluator. Score the given prompt on three dimensions from 0-100:\n"
    "- clarity: How unambiguous and clear is the instruction? (100=perfectly clear, 0=completely vague)\n"
    "- specificity: How specific and constrained is the task? (100=very specific, 0=open-ended)\n"
    "- hallucination_resistance: Does the prompt instruct the model to ground its answer, "
    "acknowledge uncertainty, or constrain scope? (100=strong grounding, 0=none)\n"
    "Return ONLY a JSON object with these three integer fields."
)


class Scorer:
    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def score(self, prompt: str) -> dict:
        token_efficiency = self._score_token_efficiency(prompt)
        format_control = self._score_format_control(prompt)
        llm_scores = self.adapter.call_structured_with_retry(
            SCORE_SYSTEM, f"Score this prompt:\n\n{prompt}", SCORE_SCHEMA
        )
        clarity = max(0, min(100, llm_scores["clarity"]))
        specificity = max(0, min(100, llm_scores["specificity"]))
        hallucination_resistance = max(0, min(100, llm_scores["hallucination_resistance"]))
        overall = int(
            (token_efficiency + format_control + clarity + specificity + hallucination_resistance)
            / 5
        )
        return {
            "token_efficiency": token_efficiency,
            "format_control": format_control,
            "clarity": clarity,
            "specificity": specificity,
            "hallucination_resistance": hallucination_resistance,
            "overall": overall,
        }

    def _score_token_efficiency(self, prompt: str) -> int:
        if self.tokenizer:
            count = len(self.tokenizer.encode(prompt))
        else:
            count = len(prompt) // 4
        # 50 tokens → 100, 550 tokens → 0
        return max(0, min(100, int(100 - (count - 50) / 5)))

    def _score_format_control(self, prompt: str) -> int:
        lower = prompt.lower()
        matches = sum(1 for p in FORMAT_PATTERNS if re.search(p, lower))
        return min(100, matches * 25)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_scorer.py -v
```

Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/scorer.py backend/tests/test_scorer.py
git commit -m "feat: add Scorer with heuristic and LLM-based dimension scoring"
```

---

## Task 7: GEPAEngine

**Files:**
- Create: `backend/src/gepa_engine.py`
- Test: `backend/tests/test_gepa_engine.py`

- [ ] **Step 1: Write the failing test `backend/tests/test_gepa_engine.py`**

```python
import pytest
from src.gepa_engine import GEPAEngine, Candidate
from src.llm_adapter import LLMAdapter


class MockAdapter(LLMAdapter):
    def call(self, system: str, user: str) -> str:
        if "weakness" in system.lower() or "diagnose" in system.lower() or "analyze" in system.lower():
            return "needs clearer output format"
        return "improved: be specific, return JSON, only use provided data"

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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_gepa_engine.py -v
```

Expected: `ImportError: cannot import name 'GEPAEngine'`

- [ ] **Step 3: Write `backend/src/gepa_engine.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_gepa_engine.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/gepa_engine.py backend/tests/test_gepa_engine.py
git commit -m "feat: add GEPAEngine with Pareto-aware evolutionary loop"
```

---

## Task 8: FastAPI endpoint

**Files:**
- Create: `backend/src/main.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Write the failing test `backend/tests/test_api.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_api.py -v
```

Expected: `ImportError: cannot import name 'app'`

- [ ] **Step 3: Write `backend/src/main.py`**

```python
import json

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
    depth: str = "quick"
    target_model: str = "generic"
    backend: str = "claude"

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("prompt must not be empty")
        return v


def get_adapter(backend: str, config) -> LLMAdapter:
    if backend == "claude":
        return ClaudeAdapter(api_key=config.claude_api_key, model=config.claude_model)
    return OllamaAdapter(base_url=config.ollama_base_url, model=config.ollama_model)


@app.post("/api/improve")
async def improve_prompt(request: ImproveRequest):
    config = get_config()
    generations = 2 if request.depth == "quick" else 5

    def generate():
        try:
            adapter = get_adapter(request.backend, config)
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
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/test_api.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Run the full backend test suite**

```bash
cd backend && source .venv/bin/activate && python -m pytest -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/main.py backend/tests/test_api.py
git commit -m "feat: add FastAPI app with SSE /api/improve endpoint"
```

---

## Task 9: Frontend types and useImprove hook

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/hooks/useImprove.ts`

- [ ] **Step 1: Write `frontend/src/types.ts`**

```typescript
export interface Scores {
  token_efficiency: number;
  format_control: number;
  clarity: number;
  specificity: number;
  hallucination_resistance: number;
  overall: number;
}

export interface Candidate {
  prompt: string;
  scores: Scores;
  reflection: string;
  generation: number;
}

export interface GenerationEvent {
  type: "generation" | "done" | "error";
  generation: number;
  prompt: string;
  scores: Scores;
  reflection: string;
  top_candidates?: Candidate[];
  message?: string;
}

export interface ImproveConfig {
  depth: "quick" | "thorough";
  target_model: string;
  backend: "claude" | "ollama";
}
```

- [ ] **Step 2: Write `frontend/src/hooks/useImprove.ts`**

```typescript
import { useState, useCallback } from "react";
import { Candidate, GenerationEvent, ImproveConfig } from "../types";

export function useImprove() {
  const [events, setEvents] = useState<GenerationEvent[]>([]);
  const [topCandidates, setTopCandidates] = useState<Candidate[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const improve = useCallback(async (prompt: string, config: ImproveConfig) => {
    setEvents([]);
    setTopCandidates([]);
    setError(null);
    setIsRunning(true);

    try {
      const response = await fetch("/api/improve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, ...config }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        for (const line of text.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const event: GenerationEvent = JSON.parse(line.slice(6));
          setEvents((prev) => [...prev, event]);
          if (event.type === "done" && event.top_candidates) {
            setTopCandidates(event.top_candidates);
          }
          if (event.type === "error") {
            setError(event.message ?? "Unknown error");
          }
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsRunning(false);
    }
  }, []);

  return { events, topCandidates, isRunning, error, improve };
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors (App.tsx doesn't exist yet — create a stub if needed: `touch src/App.tsx`)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/hooks/useImprove.ts
git commit -m "feat: add TypeScript types and useImprove SSE hook"
```

---

## Task 10: ScoreBar component

**Files:**
- Create: `frontend/src/components/ScoreBar.tsx`

- [ ] **Step 1: Write `frontend/src/components/ScoreBar.tsx`**

```tsx
const DIMENSION_LABELS: Record<string, string> = {
  token_efficiency: "Token Efficiency",
  format_control: "Format Control",
  clarity: "Clarity",
  specificity: "Specificity",
  hallucination_resistance: "Hallucination Resistance",
  overall: "Overall",
};

function colorForScore(score: number): string {
  if (score >= 70) return "bg-green-500";
  if (score >= 40) return "bg-yellow-500";
  return "bg-red-500";
}

interface ScoreBarProps {
  label: string;
  value: number;
  prevValue?: number;
}

export function ScoreBar({ label, value, prevValue }: ScoreBarProps) {
  const displayLabel = DIMENSION_LABELS[label] ?? label;
  const delta = prevValue !== undefined ? value - prevValue : null;

  return (
    <div className="mb-2">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{displayLabel}</span>
        <span className="font-mono font-semibold">
          {value}
          {delta !== null && (
            <span className={delta >= 0 ? "text-green-600 ml-1" : "text-red-600 ml-1"}>
              {delta >= 0 ? `+${delta}` : delta}
            </span>
          )}
        </span>
      </div>
      <div className="h-2 bg-gray-200 rounded">
        <div
          className={`h-2 rounded transition-all duration-500 ${colorForScore(value)}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ScoreBar.tsx
git commit -m "feat: add ScoreBar component with delta indicator"
```

---

## Task 11: InputPanel component

**Files:**
- Create: `frontend/src/components/InputPanel.tsx`

- [ ] **Step 1: Write `frontend/src/components/InputPanel.tsx`**

```tsx
import { useState } from "react";
import { ImproveConfig } from "../types";

interface InputPanelProps {
  onSubmit: (prompt: string, config: ImproveConfig) => void;
  isRunning: boolean;
}

export function InputPanel({ onSubmit, isRunning }: InputPanelProps) {
  const [prompt, setPrompt] = useState("");
  const [config, setConfig] = useState<ImproveConfig>({
    depth: "quick",
    target_model: "",
    backend: "claude",
  });
  const [validationError, setValidationError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) {
      setValidationError("Prompt cannot be empty.");
      return;
    }
    setValidationError(null);
    onSubmit(prompt, config);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl shadow p-6 flex flex-col gap-4"
    >
      <h2 className="text-lg font-semibold text-gray-800">Input Prompt</h2>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Paste your prompt here..."
        rows={6}
        className="w-full border border-gray-300 rounded-lg p-3 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />

      {validationError && (
        <p className="text-red-600 text-sm">{validationError}</p>
      )}

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Backend
          </label>
          <select
            value={config.backend}
            onChange={(e) =>
              setConfig({ ...config, backend: e.target.value as "claude" | "ollama" })
            }
            className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="claude">Claude</option>
            <option value="ollama">Ollama (local)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Depth
          </label>
          <select
            value={config.depth}
            onChange={(e) =>
              setConfig({ ...config, depth: e.target.value as "quick" | "thorough" })
            }
            className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="quick">Quick (2 generations)</option>
            <option value="thorough">Thorough (5 generations)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Target model (optional)
          </label>
          <input
            type="text"
            value={config.target_model}
            onChange={(e) => setConfig({ ...config, target_model: e.target.value })}
            placeholder="e.g. llama3.2"
            className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={isRunning}
        className="w-full bg-indigo-600 text-white font-semibold py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isRunning ? "Improving..." : "Improve Prompt"}
      </button>
    </form>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/InputPanel.tsx
git commit -m "feat: add InputPanel with backend/depth/target-model selectors"
```

---

## Task 12: EvolutionViewer component

**Files:**
- Create: `frontend/src/components/EvolutionViewer.tsx`

- [ ] **Step 1: Write `frontend/src/components/EvolutionViewer.tsx`**

```tsx
import { GenerationEvent, Scores } from "../types";
import { ScoreBar } from "./ScoreBar";

const SCORE_KEYS: (keyof Scores)[] = [
  "token_efficiency",
  "format_control",
  "clarity",
  "specificity",
  "hallucination_resistance",
];

interface EvolutionViewerProps {
  events: GenerationEvent[];
  isRunning: boolean;
}

export function EvolutionViewer({ events, isRunning }: EvolutionViewerProps) {
  const generationEvents = events.filter((e) => e.type === "generation");

  if (generationEvents.length === 0 && !isRunning) return null;

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Evolution Progress
        {isRunning && (
          <span className="ml-2 text-sm text-indigo-500 animate-pulse">
            Running...
          </span>
        )}
      </h2>

      <div className="space-y-4">
        {generationEvents.map((event, idx) => {
          const prev = idx > 0 ? generationEvents[idx - 1].scores : undefined;
          return (
            <div
              key={event.generation}
              className="border border-gray-100 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-700">
                  {event.generation === 0
                    ? "Original"
                    : `Generation ${event.generation}`}
                </span>
                <span className="text-xs text-gray-400 font-mono">
                  Overall: {event.scores.overall}
                </span>
              </div>

              {SCORE_KEYS.map((key) => (
                <ScoreBar
                  key={key}
                  label={key}
                  value={event.scores[key]}
                  prevValue={prev?.[key]}
                />
              ))}

              {event.reflection && event.generation > 0 && (
                <div className="mt-3 p-3 bg-gray-50 rounded text-xs text-gray-600 italic">
                  <span className="font-semibold not-italic text-gray-700">
                    Reflection:{" "}
                  </span>
                  {event.reflection}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/EvolutionViewer.tsx
git commit -m "feat: add EvolutionViewer with live per-generation score bars"
```

---

## Task 13: ResultsPanel component

**Files:**
- Create: `frontend/src/components/ResultsPanel.tsx`

- [ ] **Step 1: Write `frontend/src/components/ResultsPanel.tsx`**

```tsx
import * as Diff from "diff";
import { Candidate, Scores } from "../types";
import { ScoreBar } from "./ScoreBar";

const SCORE_KEYS: (keyof Scores)[] = [
  "token_efficiency",
  "format_control",
  "clarity",
  "specificity",
  "hallucination_resistance",
];

function DiffView({ original, improved }: { original: string; improved: string }) {
  const parts = Diff.diffWords(original, improved);
  return (
    <pre className="whitespace-pre-wrap font-mono text-xs bg-gray-50 rounded p-3 leading-relaxed">
      {parts.map((part, i) => (
        <span
          key={i}
          className={
            part.added
              ? "bg-green-100 text-green-800"
              : part.removed
              ? "bg-red-100 text-red-800 line-through"
              : "text-gray-700"
          }
        >
          {part.value}
        </span>
      ))}
    </pre>
  );
}

interface ResultsPanelProps {
  topCandidates: Candidate[];
  originalPrompt: string;
  originalScores?: Scores;
}

export function ResultsPanel({
  topCandidates,
  originalPrompt,
  originalScores,
}: ResultsPanelProps) {
  if (topCandidates.length === 0) return null;

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
  }

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Top Results ({topCandidates.length})
      </h2>

      <div className="space-y-6">
        {topCandidates.map((candidate, idx) => (
          <div key={idx} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-indigo-700">
                #{idx + 1} — Generation {candidate.generation} — Overall:{" "}
                {candidate.scores.overall}
              </span>
              <button
                onClick={() => copyToClipboard(candidate.prompt)}
                className="text-xs text-indigo-600 hover:text-indigo-800 border border-indigo-200 rounded px-2 py-1 transition-colors"
              >
                Copy
              </button>
            </div>

            <div className="mb-3">
              {SCORE_KEYS.map((key) => (
                <ScoreBar
                  key={key}
                  label={key}
                  value={candidate.scores[key]}
                  prevValue={originalScores?.[key]}
                />
              ))}
            </div>

            <div className="mb-3">
              <p className="text-xs font-medium text-gray-500 mb-1">
                What changed:
              </p>
              <DiffView original={originalPrompt} improved={candidate.prompt} />
            </div>

            <div className="p-3 bg-indigo-50 rounded text-sm text-gray-800 font-mono">
              {candidate.prompt}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ResultsPanel.tsx
git commit -m "feat: add ResultsPanel with word diff and copy button"
```

---

## Task 14: App root and smoke test

**Files:**
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Write `frontend/src/App.tsx`**

```tsx
import { useImprove } from "./hooks/useImprove";
import { InputPanel } from "./components/InputPanel";
import { EvolutionViewer } from "./components/EvolutionViewer";
import { ResultsPanel } from "./components/ResultsPanel";
import { ImproveConfig, Scores } from "./types";
import { useState } from "react";

export default function App() {
  const { events, topCandidates, isRunning, error, improve } = useImprove();
  const [originalPrompt, setOriginalPrompt] = useState("");

  function handleSubmit(prompt: string, config: ImproveConfig) {
    setOriginalPrompt(prompt);
    improve(prompt, config);
  }

  const gen0Scores = events.find((e) => e.generation === 0)?.scores as Scores | undefined;

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Prompt Improver</h1>
          <p className="text-gray-500 mt-1 text-sm">
            GEPA-powered evolutionary prompt optimization
          </p>
        </div>

        <InputPanel onSubmit={handleSubmit} isRunning={isRunning} />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
            Error: {error}
          </div>
        )}

        <EvolutionViewer events={events} isRunning={isRunning} />

        <ResultsPanel
          topCandidates={topCandidates}
          originalPrompt={originalPrompt}
          originalScores={gen0Scores}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors

- [ ] **Step 3: Start the backend**

```bash
cd backend && source .venv/bin/activate
cp .env.example .env
# Edit .env: set CLAUDE_API_KEY=your-key  OR  set BACKEND=ollama
uvicorn src.main:app --reload --port 8000
```

Expected: `Uvicorn running on http://127.0.0.1:8000`

- [ ] **Step 4: Start the frontend**

```bash
cd frontend && npm run dev
```

Expected: `Local: http://localhost:5173/`

- [ ] **Step 5: Smoke test in browser**

Open `http://localhost:5173`. Paste this prompt:
```
Tell me about Python.
```

Select backend (Claude or Ollama), click "Improve Prompt". Verify:
1. Evolution Viewer appears and shows "Original" card with 5 dimension scores
2. Generation 1 card appears with updated scores and a reflection note
3. Generation 2 card appears (for quick depth)
4. Results panel shows top candidate(s) with diff view (green = added, red+strikethrough = removed) and copy button

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: wire up App root — prompt improver complete"
```
