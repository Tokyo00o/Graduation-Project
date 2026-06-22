import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class RateLimitError(Exception):
    pass


class ProviderError(Exception):
    pass


class BaseProvider(ABC):
    name: str = ""
    default_model: str = ""

    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key
        self.model = model or self.default_model
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset: Optional[float] = None

    @abstractmethod
    def _call(self, prompt: str) -> Dict:
        ...

    def _format_messages_as_prompt(self, messages: List[Dict]) -> str:
        lines = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            label = "User" if role == "user" else "Assistant"
            lines.append(f"{label}: {content}")
        return "\n".join(lines)

    def _call_messages(self, messages: List[Dict]) -> Dict:
        return self._call(self._format_messages_as_prompt(messages))

    def query(self, prompt: str = "", messages: Optional[List[Dict]] = None) -> Dict:
        self._check_rate_limit()
        try:
            if messages is not None:
                result = self._call_messages_with_retry(messages)
            else:
                result = self._call_with_retry(prompt)
            self._update_rate_limit(result)
            return result
        except RateLimitError:
            return self._fallback_response("Rate limited by provider")
        except ProviderError as e:
            return self._fallback_response(str(e))

    @retry(
        retry=retry_if_exception_type((RateLimitError, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=30),
    )
    def _call_with_retry(self, prompt: str) -> Dict:
        return self._call(prompt)

    @retry(
        retry=retry_if_exception_type((RateLimitError, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=30),
    )
    def _call_messages_with_retry(self, messages: List[Dict]) -> Dict:
        return self._call_messages(messages)

    def _check_rate_limit(self):
        if self._rate_limit_reset and time.time() < self._rate_limit_reset:
            sleep_time = self._rate_limit_reset - time.time()
            if sleep_time > 0:
                time.sleep(min(sleep_time, 5))

    def _update_rate_limit(self, result: Dict):
        headers = result.get("_headers", {})
        remaining = headers.get("x-ratelimit-remaining")
        if remaining is not None:
            self._rate_limit_remaining = int(remaining)
        reset_time = headers.get("x-ratelimit-reset")
        if reset_time is not None:
            self._rate_limit_reset = time.time() + int(reset_time)

    def _fallback_response(self, reason: str) -> Dict:
        return {
            "response": f"[Provider unavailable: {reason}]",
            "latency": 0.0,
            "status_code": "503",
            "model": self.model,
        }
