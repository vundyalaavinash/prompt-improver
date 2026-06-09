import json
import re
import shutil
import subprocess

import httpx

from .llm_adapter import LLMAdapter

# Devin REST API base — verify at https://docs.cognition.ai when you have tokens
DEVIN_API_URL = "https://api.cognition.ai/v1"


class DevinAdapter(LLMAdapter):
    """
    Devin adapter — two modes, tried in order:

    1. CLI mode  (no tokens needed): requires `devin` binary on PATH.
       Calls: devin run --print "<prompt>"
       Update DEVIN_CLI_CMD in config if Cognition changes the CLI syntax.

    2. API mode  (tokens needed): set DEVIN_API_KEY in .env.
       Uses OpenAI-compatible /chat/completions endpoint.
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "devin",
        base_url: str = DEVIN_API_URL,
        cli_cmd: str = "devin",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.cli_cmd = cli_cmd
        self._cli_available = shutil.which(cli_cmd) is not None

    def call(self, system: str, user: str) -> str:
        if self._cli_available:
            return self._call_cli(system, user)
        if self.api_key:
            return self._call_api(system, user)
        raise RuntimeError(
            "Devin is not available: `devin` CLI not found on PATH and DEVIN_API_KEY is not set. "
            "Install the Devin CLI or add DEVIN_API_KEY to backend/.env."
        )

    def _call_cli(self, system: str, user: str) -> str:
        # Devin CLI: `devin run --print "<full prompt>"`
        # The system prompt is prepended to the user message since the CLI
        # may not have a dedicated --system-prompt flag.
        full_prompt = f"{system}\n\n{user}"
        result = subprocess.run(
            [self.cli_cmd, "run", "--print", full_prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"devin CLI error: {result.stderr.strip()}")
        return result.stdout.strip()

    def _call_api(self, system: str, user: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

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
