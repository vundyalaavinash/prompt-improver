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
