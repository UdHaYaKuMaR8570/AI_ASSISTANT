from dataclasses import dataclass
from typing import Optional

from app.config import Settings
from app.errors import AppError


@dataclass
class ResolvedProvider:
    provider: str
    model: str
    base_url: str
    api_key: Optional[str]
    headers: dict[str, str]


def resolve_provider(settings: Settings, provider_name: str, model_override: Optional[str] = None) -> ResolvedProvider:
    provider = provider_name.lower().strip()

    if provider == "ollama":
        model = model_override or settings.ollama_model
        return ResolvedProvider(
            provider="ollama",
            model=model,
            base_url=f"{settings.ollama_host.rstrip('/')}/v1",
            api_key="ollama",
            headers={"Content-Type": "application/json"},
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise AppError(
                code="provider_unavailable",
                message="Anthropic provider requested but ANTHROPIC_API_KEY is not configured",
                status_code=502,
                detail={"provider": "anthropic"},
            )
        model = model_override or settings.anthropic_model
        return ResolvedProvider(
            provider="anthropic",
            model=model,
            base_url="https://api.anthropic.com/v1",
            api_key=settings.anthropic_api_key,
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise AppError(
                code="provider_unavailable",
                message="OpenAI provider requested but OPENAI_API_KEY is not configured",
                status_code=502,
                detail={"provider": "openai"},
            )
        model = model_override or settings.openai_model
        return ResolvedProvider(
            provider="openai",
            model=model,
            base_url="https://api.openai.com/v1",
            api_key=settings.openai_api_key,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
        )

    if provider == "custom":
        if not (settings.custom_base_url and settings.custom_api_key):
            raise AppError(
                code="provider_unavailable",
                message="Custom provider requested but CUSTOM_BASE_URL or CUSTOM_API_KEY is not configured",
                status_code=502,
                detail={"provider": "custom"},
            )
        model = model_override or settings.custom_model or "custom-model"
        return ResolvedProvider(
            provider="custom",
            model=model,
            base_url=settings.custom_base_url.rstrip("/"),
            api_key=settings.custom_api_key,
            headers={
                "Authorization": f"Bearer {settings.custom_api_key}",
                "Content-Type": "application/json",
            },
        )

    raise AppError(
        code="unknown_provider",
        message=f"Unknown LLM provider: '{provider}'. Supported providers are: ollama, anthropic, openai, custom",
        status_code=400,
        detail={"requested_provider": provider},
    )
