from typing import Any

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
async def get_config(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    return {
        "default_provider": settings.llm_provider,
        "default_model": {
            "ollama": settings.ollama_model,
            "anthropic": settings.anthropic_model,
            "openai": settings.openai_model,
            "custom": settings.custom_model or "custom-model",
        },
        "embed_model": settings.embed_model,
        "agent_mode": settings.agent_mode,
        "available_providers": [
            {"id": "ollama", "name": "Local Ollama", "model": settings.ollama_model, "requires_key": False},
            {"id": "anthropic", "name": "Anthropic Claude", "model": settings.anthropic_model, "requires_key": True},
            {"id": "openai", "name": "OpenAI", "model": settings.openai_model, "requires_key": True},
            {"id": "custom", "name": "Custom Endpoint", "model": settings.custom_model or "custom", "requires_key": True},
        ],
    }
