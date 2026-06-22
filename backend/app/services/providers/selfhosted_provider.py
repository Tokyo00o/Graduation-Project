import json
import os
from typing import Dict, List

import httpx

from app.services.providers.base import BaseProvider, ProviderError, RateLimitError


class SelfHostedProvider(BaseProvider):
    name = "selfhosted"
    default_model = ""

    def __init__(self, api_key: str = "", model: str = "", base_url: str = ""):
        super().__init__(api_key or os.getenv("SELFHOSTED_API_KEY", ""), model)
        self.base_url = base_url or os.getenv("SELFHOSTED_BASE_URL", "http://localhost:8000/v1")

    def _call(self, prompt: str) -> Dict:
        return self._call_messages([{"role": "user", "content": prompt}])

    def _call_messages(self, messages: List[Dict]) -> Dict:
        url = f"{self.base_url.rstrip('/')}/chat/completions"

        try:
            resp = httpx.post(
                url,
                json={
                    "model": self.model or "default",
                    "messages": messages,
                    "max_tokens": 512,
                    "temperature": 1.0,
                },
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
        except httpx.TimeoutException:
            raise ProviderError("Self-hosted request timed out")
        except httpx.RequestError as e:
            raise ProviderError(f"Self-hosted request failed: {e}")

        if resp.status_code == 429:
            raise RateLimitError("Self-hosted rate limited")
        if resp.status_code != 200:
            raise ProviderError(f"Self-hosted returned {resp.status_code}: {resp.text}")

        data = resp.json()
        choice = data.get("choices", [{}])[0].get("message", {})

        return {
            "response": choice.get("content", ""),
            "latency": resp.elapsed.total_seconds(),
            "status_code": str(resp.status_code),
            "model": self.model or "self-hosted",
            "_headers": dict(resp.headers),
        }
