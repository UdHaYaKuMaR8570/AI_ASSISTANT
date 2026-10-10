import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent.service import AgentService
from app.errors import AppError
from app.repos import ArtifactRepo, MessageRepo, SessionRepo
from app.routes.deps import (
    get_agent_service,
    get_artifact_repo,
    get_message_repo,
    get_session_repo,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., description="Anonymous client user identifier")
    provider: str = Field(default="ollama", description="LLM provider: ollama | anthropic | openai | custom")
    model: str = Field(default="qwen3:4b", description="Model name")
    title: str = Field(default="New Conversation", description="Session title")


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, description="User prompt text")


class SessionResponse(BaseModel):
    id: str
    user_id: str
    provider: str
    model: str
    title: str
    created_at: str
    updated_at: str


@router.post("", status_code=201)
async def create_session(
    body: CreateSessionRequest,
    repo: SessionRepo = Depends(get_session_repo),
) -> dict[str, Any]:
    session = await repo.create(
        provider=body.provider,
        model=body.model,
        user_id=body.user_id,
        title=body.title,
    )
    await repo.db.commit()
    return {
        "id": str(session.id),
        "user_id": session.user_id,
        "provider": session.provider,
        "model": session.model,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.get("")
async def list_sessions(
    user_id: str = Query(..., description="User ID to list sessions for"),
    repo: SessionRepo = Depends(get_session_repo),
) -> list[dict[str, Any]]:
    sessions = await repo.list(user_id=user_id)
    return [
        {
            "id": str(s.id),
            "user_id": s.user_id,
            "provider": s.provider,
            "model": s.model,
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/{session_id}")
async def get_session(
    session_id: uuid.UUID,
    session_repo: SessionRepo = Depends(get_session_repo),
    message_repo: MessageRepo = Depends(get_message_repo),
    artifact_repo: ArtifactRepo = Depends(get_artifact_repo),
) -> dict[str, Any]:
    session = await session_repo.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await message_repo.for_session(session_id)
    artifacts = await artifact_repo.groups_for_session(session_id)

    return {
        "session": {
            "id": str(session.id),
            "user_id": session.user_id,
            "provider": session.provider,
            "model": session.model,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        },
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "citations": m.citations,
                "stats": m.stats,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "artifacts": [
            {
                "id": a.id,
                "group_id": str(a.artifact_group_id),
                "version": a.version,
                "kind": a.kind,
                "title": a.title,
                "content": a.content,
                "change_note": a.change_note,
                "created_at": a.created_at.isoformat(),
            }
            for a in artifacts
        ],
    }


@router.delete("/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    repo: SessionRepo = Depends(get_session_repo),
) -> dict[str, Any]:
    deleted = await repo.soft_delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    await repo.db.commit()
    return {"status": "deleted", "id": str(session_id)}


@router.post("/{session_id}/messages")
async def send_message(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    generator = service.stream_turn(session_id, body.content)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{session_id}/artifacts")
async def get_session_artifacts(
    session_id: uuid.UUID,
    repo: ArtifactRepo = Depends(get_artifact_repo),
) -> list[dict[str, Any]]:
    artifacts = await repo.groups_for_session(session_id)
    return [
        {
            "id": a.id,
            "group_id": str(a.artifact_group_id),
            "version": a.version,
            "kind": a.kind,
            "title": a.title,
            "content": a.content,
            "change_note": a.change_note,
            "created_at": a.created_at.isoformat(),
        }
        for a in artifacts
    ]
