import json
import os
from typing import Dict

import httpx

from app.services.providers.base import BaseProvider, ProviderError, RateLimitError

BASE_URL = "https://api.cohere.ai/v1/chat"

MODEL_MAP = {
    "command-r": "command-r",
    "command-r-plus": "command-r-plus",
    "command": "command",
    "command-light": "command-light",
}


class CohereProvider(BaseProvider):
    name = "cohere"
    default_model = "command-r"

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key or os.getenv("COHERE_API_KEY", ""), model)

    def _call(self, prompt: str) -> Dict:
        if not self.api_key:
            return self._fallback_response("No Cohere API key configured")

        try:
            resp = httpx.post(
                BASE_URL,
                json={
                    "model": MODEL_MAP.get(self.model, self.model),
                    "message": prompt,
                    "max_tokens": 512,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
        except httpx.TimeoutException:
            raise ProviderError("Cohere request timed out")
        except httpx.RequestError as e:
            raise ProviderError(f"Cohere request failed: {e}")

        if resp.status_code == 429:
            raise RateLimitError("Cohere rate limited")
        if resp.status_code != 200:
            raise ProviderError(f"Cohere returned {resp.status_code}: {resp.text}")

        data = resp.json()
        return {
            "response": data.get("text", ""),
            "latency": resp.elapsed.total_seconds(),
            "status_code": str(resp.status_code),
            "model": self.model,
            "_headers": dict(resp.headers),
        }
