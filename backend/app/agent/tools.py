import json
import uuid
from typing import Any, Callable, Coroutine, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunk, Episode
from app.repos import ArtifactRepo
from app.retrieval.embedder import OllamaEmbedder
from app.retrieval.search import format_youtube_timestamp_url, hybrid_search

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_transcripts",
            "description": "Searches Lenny's Podcast transcripts for relevant passages, guest wisdom, and frameworks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'retention curves', 'pricing experiments', 'founder market fit').",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of relevant chunks to retrieve (default: 6).",
                        "default": 6,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_episode_context",
            "description": "Retrieves adjacent context or turns from a specific episode around a timestamp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "episode_slug": {
                        "type": "string",
                        "description": "The slug of the episode.",
                    },
                    "around_ts": {
                        "type": "integer",
                        "description": "Timestamp in seconds around which to fetch context.",
                    },
                    "window": {
                        "type": "integer",
                        "description": "Number of neighboring chunks before and after (default: 2).",
                        "default": 2,
                    },
                },
                "required": ["episode_slug", "around_ts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_artifact",
            "description": "Creates a new standalone, versioned artifact document (Markdown essay/PRD/roadmap or interactive HTML tool).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the artifact.",
                    },
                    "kind": {
                        "type": "string",
                        "enum": ["markdown", "html"],
                        "description": "Format of the artifact: 'markdown' or 'html'.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full content of the artifact.",
                    },
                },
                "required": ["title", "kind", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_artifact",
            "description": "Updates an existing artifact by creating a new version in its group.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "UUID of the artifact group to update.",
                    },
                    "content": {
                        "type": "string",
                        "description": "New content for the artifact.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional updated title.",
                    },
                    "change_note": {
                        "type": "string",
                        "description": "Summary of what changed (e.g., 'Made tone more concise', 'Added ROI calculator').",
                    },
                },
                "required": ["group_id", "content"],
            },
        },
    },
]


async def execute_tool(
    name: str,
    arguments: dict[str, Any],
    db: AsyncSession,
    embedder: OllamaEmbedder,
    session_id: uuid.UUID,
    artifact_callback: Optional[Callable[[dict[str, Any]], Coroutine[Any, Any, None]]] = None,
) -> dict[str, Any]:
    """Executes an in-process tool and returns structured result payload."""
    if name == "search_transcripts":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 6)
        chunks = await hybrid_search(db, embedder, query, top_k=top_k)
        if not chunks:
            return {"status": "no_results", "message": "No relevant transcript passages found."}
        return {
            "status": "success",
            "results": [c.to_dict() for c in chunks],
        }

    if name == "get_episode_context":
        episode_slug = arguments.get("episode_slug", "")
        around_ts = arguments.get("around_ts", 0)
        window = arguments.get("window", 2)

        ep_res = await db.execute(select(Episode).where(Episode.slug == episode_slug))
        ep = ep_res.scalar_one_or_none()
        if not ep:
            return {"status": "error", "message": f"Episode '{episode_slug}' not found."}

        stmt = (
            select(Chunk)
            .where(Chunk.episode_id == ep.id)
            .order_by(Chunk.chunk_index.asc())
        )
        res = await db.execute(stmt)
        all_chunks = list(res.scalars().all())

        # Find closest chunk by start_ts
        closest_idx = 0
        min_diff = float("inf")
        for i, c in enumerate(all_chunks):
            diff = abs((c.start_ts or 0) - around_ts)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i

        start_slice = max(0, closest_idx - window)
        end_slice = min(len(all_chunks), closest_idx + window + 1)
        slice_chunks = all_chunks[start_slice:end_slice]

        return {
            "status": "success",
            "episode": {"slug": ep.slug, "title": ep.title, "guest": ep.guest},
            "context": [
                {
                    "chunk_id": c.id,
                    "chunk_index": c.chunk_index,
                    "speaker": c.speaker,
                    "start_ts": c.start_ts,
                    "youtube_url": format_youtube_timestamp_url(ep.youtube_url, c.start_ts),
                    "text": c.text,
                }
                for c in slice_chunks
            ],
        }

    if name == "create_artifact":
        repo = ArtifactRepo(db)
        title = arguments.get("title", "Untitled")
        kind = arguments.get("kind", "markdown")
        content = arguments.get("content", "")
        artifact = await repo.create(session_id=session_id, kind=kind, title=title, content=content)
        await db.commit()

        payload = {
            "id": artifact.id,
            "group_id": str(artifact.artifact_group_id),
            "version": artifact.version,
            "kind": artifact.kind,
            "title": artifact.title,
            "content": artifact.content,
        }
        if artifact_callback:
            await artifact_callback(payload)
        return {"status": "success", "artifact": payload}

    if name == "update_artifact":
        repo = ArtifactRepo(db)
        group_id_str = arguments.get("group_id", "")
        group_id = uuid.UUID(group_id_str)
        content = arguments.get("content", "")
        title = arguments.get("title")
        change_note = arguments.get("change_note")

        artifact = await repo.add_version(
            group_id=group_id,
            content=content,
            title=title,
            change_note=change_note,
        )
        await db.commit()

        payload = {
            "id": artifact.id,
            "group_id": str(artifact.artifact_group_id),
            "version": artifact.version,
            "kind": artifact.kind,
            "title": artifact.title,
            "content": artifact.content,
            "change_note": artifact.change_note,
        }
        if artifact_callback:
            await artifact_callback(payload)
        return {"status": "success", "artifact": payload}

    return {"status": "error", "message": f"Unknown tool: {name}"}
