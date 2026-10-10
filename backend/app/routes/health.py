from typing import Any

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.probes import run_all_probes

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def get_health(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    return await run_all_probes(settings)
