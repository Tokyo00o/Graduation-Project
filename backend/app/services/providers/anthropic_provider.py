import json
import os
from typing import Dict, List

import httpx

from app.services.providers.base import BaseProvider, ProviderError, RateLimitError

BASE_URL = "https://api.anthropic.com/v1/messages"

MODEL_MAP = {
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-haiku": "claude-3-haiku-20240307",
    "claude-3.5-sonnet": "claude-3-5-sonnet-20241022",
    "claude-4": "claude-4-20250514",
}


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    default_model = "claude-3.5-sonnet"

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY", ""), model)

    def _call(self, prompt: str) -> Dict:
        return self._call_messages([{"role": "user", "content": prompt}])

    def _call_messages(self, messages: List[Dict]) -> Dict:
        if not self.api_key:
            return self._fallback_response("No Anthropic API key configured")

        try:
            resp = httpx.post(
                BASE_URL,
                json={
                    "model": MODEL_MAP.get(self.model, self.model),
                    "max_tokens": 512,
                    "messages": messages,
                },
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                timeout=30,
            )
        except httpx.TimeoutException:
            raise ProviderError("Anthropic request timed out")
        except httpx.RequestError as e:
            raise ProviderError(f"Anthropic request failed: {e}")

        if resp.status_code == 429:
            raise RateLimitError("Anthropic rate limited")
        if resp.status_code != 200:
            raise ProviderError(f"Anthropic returned {resp.status_code}: {resp.text}")

        data = resp.json()
        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")

        return {
            "response": text,
            "latency": resp.elapsed.total_seconds(),
            "status_code": str(resp.status_code),
            "model": self.model,
            "usage": {"input_tokens": data.get("usage", {}).get("input_tokens"), "output_tokens": data.get("usage", {}).get("output_tokens")},
            "_headers": dict(resp.headers),
        }
