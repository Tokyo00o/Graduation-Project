import json
import os
from typing import Dict

import httpx

from app.services.providers.base import BaseProvider, ProviderError, RateLimitError

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models" \
           "/{model}:generateContent?key={key}"

MODEL_MAP = {
    "gemini-pro": "gemini-pro",
    "gemini-1.5-pro": "gemini-1.5-pro",
    "gemini-1.5-flash": "gemini-1.5-flash",
    "gemini-2.0-flash": "gemini-2.0-flash",
}


class GoogleProvider(BaseProvider):
    name = "google"
    default_model = "gemini-1.5-pro"

    def __init__(self, api_key: str = "", model: str = ""):
        super().__init__(api_key or os.getenv("GOOGLE_API_KEY", ""), model)

    def _call(self, prompt: str) -> Dict:
        if not self.api_key:
            return self._fallback_response("No Google API key configured")

        api_model = MODEL_MAP.get(self.model, self.model)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{api_model}:generateContent?key={self.api_key}"

        try:
            resp = httpx.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                headers={"content-type": "application/json"},
                timeout=30,
            )
        except httpx.TimeoutException:
            raise ProviderError("Google request timed out")
        except httpx.RequestError as e:
            raise ProviderError(f"Google request failed: {e}")

        if resp.status_code == 429:
            raise RateLimitError("Google rate limited")
        if resp.status_code != 200:
            raise ProviderError(f"Google returned {resp.status_code}: {resp.text}")

        data = resp.json()
        candidates = data.get("candidates", [])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)

        return {
            "response": text,
            "latency": resp.elapsed.total_seconds(),
            "status_code": str(resp.status_code),
            "model": self.model,
            "_headers": dict(resp.headers),
        }
