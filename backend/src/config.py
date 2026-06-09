from functools import lru_cache
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    backend: str = "claude"
    claude_model: str = "sonnet"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:12b"
    devin_api_key: str = ""
    devin_base_url: str = "https://api.cognition.ai/v1"
    devin_model: str = "devin"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_config() -> Config:
    return Config()
