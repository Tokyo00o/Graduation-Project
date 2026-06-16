from typing import Dict, Optional, Type

from app.services.providers.anthropic_provider import AnthropicProvider
from app.services.providers.base import BaseProvider
from app.services.providers.cohere_provider import CohereProvider
from app.services.providers.google_provider import GoogleProvider
from app.services.providers.huggingface_provider import HuggingFaceProvider
from app.services.providers.mistral_provider import MistralProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.selfhosted_provider import SelfHostedProvider
from app.services.llm_client import MockLLMClient

PROVIDER_CLIENTS: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "cohere": CohereProvider,
    "mistral": MistralProvider,
    "huggingface": HuggingFaceProvider,
    "selfhosted": SelfHostedProvider,
}

PROVIDER_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini"],
    "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3.5-sonnet", "claude-4"],
    "google": ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"],
    "cohere": ["command-r", "command-r-plus", "command", "command-light"],
    "mistral": ["mistral-large", "mistral-small", "mistral-medium", "open-mistral-7b", "open-mixtral-8x7b"],
    "huggingface": ["custom-endpoint"],
    "selfhosted": ["custom"],
}


class ProviderRegistry:
    def __init__(self):
        self._instances: Dict[str, BaseProvider] = {}

    def get(self, provider_name: str, api_key: str = "", model: str = "") -> BaseProvider:
        cache_key = f"{provider_name}:{model}"
        if cache_key in self._instances:
            return self._instances[cache_key]

        client_cls = PROVIDER_CLIENTS.get(provider_name)
        if not client_cls:
            return MockLLMClient(jailbreak_rate=0.3)

        instance = client_cls(api_key=api_key, model=model)
        self._instances[cache_key] = instance
        return instance

    def list_providers(self) -> list:
        return [
            {"name": name, "models": models}
            for name, models in PROVIDER_MODELS.items()
        ]

    def clear_cache(self):
        self._instances.clear()


provider_registry = ProviderRegistry()
