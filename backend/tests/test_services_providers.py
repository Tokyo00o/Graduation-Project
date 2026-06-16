import pytest
from app.services.providers.registry import provider_registry, PROVIDER_MODELS


class TestNoDB:
    def test_provider_registry_has_all(self):
        providers = provider_registry.list_providers()
        names = [p["name"] for p in providers]
        assert "openai" in names
        assert "anthropic" in names
        assert "google" in names
        assert "cohere" in names
        assert "mistral" in names
        assert "huggingface" in names
        assert "selfhosted" in names

    def test_provider_registry_returns_mock_for_unknown(self):
        inst = provider_registry.get("unknown_provider")
        assert inst.__class__.__name__ == "MockLLMClient"

    def test_provider_models_defined(self):
        assert "gpt-4o" in PROVIDER_MODELS["openai"]
        assert "claude-3.5-sonnet" in PROVIDER_MODELS["anthropic"]
        assert "gemini-1.5-pro" in PROVIDER_MODELS["google"]

    def test_openai_provider_fallback_no_key(self):
        inst = provider_registry.get("openai")
        result = inst.query("test")
        assert "unavailable" in result.get("response", "").lower()

    def test_anthropic_provider_fallback_no_key(self):
        inst = provider_registry.get("anthropic")
        result = inst.query("test")
        assert "unavailable" in result.get("response", "").lower()

    def test_provider_registry_cache(self):
        a = provider_registry.get("openai", model="gpt-4o")
        b = provider_registry.get("openai", model="gpt-4o")
        assert a is b

    def test_provider_registry_cache_clear(self):
        provider_registry.clear_cache()
        a = provider_registry.get("openai", model="gpt-4o")
        b = provider_registry.get("openai", model="gpt-4o")
        assert a is b
