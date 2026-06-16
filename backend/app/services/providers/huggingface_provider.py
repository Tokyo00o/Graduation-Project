import json
import os
from typing import Dict

import httpx

from app.services.providers.base import BaseProvider, ProviderError, RateLimitError


class HuggingFaceProvider(BaseProvider):
    name = "huggingface"
    default_model = ""

    def __init__(self, api_key: str = "", model: str = "", endpoint_url: str = ""):
        super().__init__(api_key or os.getenv("HF_API_KEY", ""), model)
        self.endpoint_url = endpoint_url or os.getenv("HF_ENDPOINT_URL", "")

    def _call(self, prompt: str) -> Dict:
        if not self.api_key:
            return self._fallback_response("No HuggingFace API key configured")
        if not self.endpoint_url and not self.model:
            return self._fallback_response("No HuggingFace endpoint or model configured")

        url = self.endpoint_url or f"https://api-inference.huggingface.co/models/{self.model}"
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 512, "temperature": 1.0}}

        try:
            resp = httpx.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=60,
            )
        except httpx.TimeoutException:
            raise ProviderError("HuggingFace request timed out")
        except httpx.RequestError as e:
            raise ProviderError(f"HuggingFace request failed: {e}")

        if resp.status_code == 429:
            raise RateLimitError("HuggingFace rate limited")
        if resp.status_code != 200:
            raise ProviderError(f"HuggingFace returned {resp.status_code}: {resp.text}")

        data = resp.json()
        text = ""
        if isinstance(data, list):
            text = data[0].get("generated_text", "")
        elif isinstance(data, dict):
            text = data.get("generated_text", "")

        return {
            "response": text,
            "latency": resp.elapsed.total_seconds(),
            "status_code": str(resp.status_code),
            "model": self.model or "huggingface",
            "_headers": dict(resp.headers),
        }
