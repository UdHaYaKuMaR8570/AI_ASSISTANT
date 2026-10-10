from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.service import AgentService
from app.config import Settings, get_settings
from app.db import get_db
from app.repos import ArtifactRepo, MessageRepo, SessionRepo


def get_session_repo(db: AsyncSession = Depends(get_db)) -> SessionRepo:
    return SessionRepo(db)


def get_message_repo(db: AsyncSession = Depends(get_db)) -> MessageRepo:
    return MessageRepo(db)


def get_artifact_repo(db: AsyncSession = Depends(get_db)) -> ArtifactRepo:
    return ArtifactRepo(db)


def get_agent_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AgentService:
    return AgentService(db, settings)
