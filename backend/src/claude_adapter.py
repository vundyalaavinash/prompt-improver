import json
import re

import httpx

from .llm_adapter import LLMAdapter

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class ClaudeAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model

    def call(self, system: str, user: str) -> str:
        response = httpx.post(
            CLAUDE_API_URL,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 1024,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]

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
