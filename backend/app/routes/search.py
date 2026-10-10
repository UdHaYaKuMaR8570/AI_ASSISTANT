from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_db
from app.retrieval.embedder import OllamaEmbedder
from app.retrieval.search import hybrid_search

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query string")
    top_k: int = Field(default=6, ge=1, le=20, description="Max results")


@router.post("")
async def search_transcripts_endpoint(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    embedder = OllamaEmbedder(host=settings.ollama_host, model=settings.embed_model)
    chunks = await hybrid_search(db, embedder, body.query, top_k=body.top_k)
    return {
        "query": body.query,
        "count": len(chunks),
        "results": [c.to_dict() for c in chunks],
    }
