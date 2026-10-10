import asyncio
from typing import Any

import httpx
from sqlalchemy import text

from app.config import Settings
from app.db import get_engine


async def check_db() -> dict[str, Any]:
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=3.0)
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "unavailable", "detail": str(exc)}


async def check_ollama(settings: Settings) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_host.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                has_model = any(settings.ollama_model in m for m in models)
                has_embed = any(settings.embed_model in m for m in models)
                return {
                    "status": "ok",
                    "models_loaded": {
                        settings.ollama_model: has_model,
                        settings.embed_model: has_embed,
                    },
                }
            return {"status": "unavailable", "detail": f"HTTP {resp.status_code}"}
    except Exception as exc:
        return {"status": "unavailable", "detail": str(exc)}


async def check_litellm(settings: Settings) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.litellm_url.rstrip('/')}/health/liveliness")
            if resp.status_code == 200:
                return {"status": "ok"}
            return {"status": "unavailable", "detail": f"HTTP {resp.status_code}"}
    except Exception as exc:
        return {"status": "unavailable", "detail": str(exc)}


async def run_all_probes(settings: Settings) -> dict[str, Any]:
    db_res, ollama_res, litellm_res = await asyncio.gather(
        check_db(),
        check_ollama(settings),
        check_litellm(settings),
    )

    checks = {
        "db": db_res,
        "ollama": ollama_res,
        "litellm": litellm_res,
        "providers": {
            "ollama": ollama_res["status"] == "ok",
            "anthropic": bool(settings.anthropic_api_key),
            "openai": bool(settings.openai_api_key) and litellm_res["status"] == "ok",
            "custom": bool(settings.custom_base_url and settings.custom_api_key) and litellm_res["status"] == "ok",
        },
    }

    # Stack is ok if db is up and at least one LLM provider is available
    any_provider = any(checks["providers"].values())
    is_ok = db_res["status"] == "ok" and any_provider

    return {
        "status": "ok" if is_ok else "degraded",
        "checks": checks,
    }
