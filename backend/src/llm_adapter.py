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
