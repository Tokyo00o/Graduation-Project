import json
import os
import time
from typing import Dict, List, Optional

import httpx

from app.services.providers.base import BaseProvider, ProviderError, RateLimitError

BASE_URL = "https://api.openai.com/v1/chat/completions"

MODEL_ALIASES = {
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-4-turbo": "gpt-4-turbo",
    "gpt-4": "gpt-4",
    "gpt-3.5-turbo": "gpt-3.5-turbo",
    "o1": "o1",
    "o1-mini": "o1-mini",
}


class OpenAIProvider(BaseProvider):
    name = "openai"
    default_model = "gpt-4o"

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY", ""), model)
        self.base_url = os.getenv("OPENAI_BASE_URL", BASE_URL)

    def _call(self, prompt: str) -> Dict:
        return self._call_messages([{"role": "user", "content": prompt}])

    def _call_messages(self, messages: List[Dict]) -> Dict:
        if not self.api_key:
            return self._fallback_response("No OpenAI API key configured")

        try:
            resp = httpx.post(
                self.base_url,
                json={
                    "model": MODEL_ALIASES.get(self.model, self.model),
                    "messages": messages,
                    "temperature": 1.0,
                    "max_tokens": 512,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
        except httpx.TimeoutException:
            raise ProviderError("OpenAI request timed out")
        except httpx.RequestError as e:
            raise ProviderError(f"OpenAI request failed: {e}")

        if resp.status_code == 429:
            raise RateLimitError("OpenAI rate limited")
        if resp.status_code != 200:
            raise ProviderError(f"OpenAI returned {resp.status_code}: {resp.text}")

        data = resp.json()
        choice = data.get("choices", [{}])[0].get("message", {})

        return {
            "response": choice.get("content", ""),
            "latency": resp.elapsed.total_seconds(),
            "status_code": str(resp.status_code),
            "model": self.model,
            "usage": data.get("usage", {}),
            "_headers": dict(resp.headers),
        }
