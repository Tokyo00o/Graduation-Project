import json
import os
from typing import Dict, List

import httpx

from app.services.providers.base import BaseProvider, ProviderError, RateLimitError

BASE_URL = "https://api.mistral.ai/v1/chat/completions"

MODEL_MAP = {
    "mistral-large": "mistral-large-latest",
    "mistral-small": "mistral-small-latest",
    "mistral-medium": "mistral-medium-latest",
    "open-mistral-7b": "open-mistral-7b",
    "open-mixtral-8x7b": "open-mixtral-8x7b",
}


class MistralProvider(BaseProvider):
    name = "mistral"
    default_model = "mistral-large"

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key or os.getenv("MISTRAL_API_KEY", ""), model)

    def _call(self, prompt: str) -> Dict:
        return self._call_messages([{"role": "user", "content": prompt}])

    def _call_messages(self, messages: List[Dict]) -> Dict:
        if not self.api_key:
            return self._fallback_response("No Mistral API key configured")

        try:
            resp = httpx.post(
                BASE_URL,
                json={
                    "model": MODEL_MAP.get(self.model, self.model),
                    "messages": messages,
                    "max_tokens": 512,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
        except httpx.TimeoutException:
            raise ProviderError("Mistral request timed out")
        except httpx.RequestError as e:
            raise ProviderError(f"Mistral request failed: {e}")

        if resp.status_code == 429:
            raise RateLimitError("Mistral rate limited")
        if resp.status_code != 200:
            raise ProviderError(f"Mistral returned {resp.status_code}: {resp.text}")

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
