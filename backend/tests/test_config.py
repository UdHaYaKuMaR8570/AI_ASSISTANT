import pytest
from app.agent.providers import resolve_provider
from app.config import Settings
from app.errors import AppError


def test_settings_defaults():
    settings = Settings()
    assert settings.llm_provider in ("ollama", "anthropic", "openai", "custom")
    assert settings.embed_model == "nomic-embed-text"
    assert settings.ollama_model == "qwen3:4b"


def test_resolve_provider_ollama():
    settings = Settings()
    resolved = resolve_provider(settings, "ollama")
    assert resolved.provider == "ollama"
    assert "11434" in resolved.base_url


def test_resolve_provider_missing_key():
    settings = Settings(anthropic_api_key=None)
    with pytest.raises(AppError) as exc_info:
        resolve_provider(settings, "anthropic")
    assert exc_info.value.code == "provider_unavailable"
