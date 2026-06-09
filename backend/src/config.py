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
