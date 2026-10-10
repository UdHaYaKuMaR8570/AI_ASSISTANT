import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.repos import ArtifactRepo
from app.routes.deps import get_artifact_repo

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{group_id}/versions")
async def list_artifact_versions(
    group_id: uuid.UUID,
    repo: ArtifactRepo = Depends(get_artifact_repo),
) -> list[dict[str, Any]]:
    artifacts = await repo.get_all_versions(group_id)
    if not artifacts:
        raise HTTPException(status_code=404, detail="Artifact group not found")
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


@router.get("/{group_id}/versions/{version}")
async def get_artifact_version(
    group_id: uuid.UUID,
    version: int,
    repo: ArtifactRepo = Depends(get_artifact_repo),
) -> dict[str, Any]:
    artifact = await repo.get_version(group_id, version)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact version not found")
    return {
        "id": artifact.id,
        "group_id": str(artifact.artifact_group_id),
        "version": artifact.version,
        "kind": artifact.kind,
        "title": artifact.title,
        "content": artifact.content,
        "change_note": artifact.change_note,
        "created_at": artifact.created_at.isoformat(),
    }
