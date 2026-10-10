import asyncio
import json
import time
import uuid
from typing import Any, AsyncGenerator, List, Optional

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.events import (
    ArtifactEvent,
    CitationEvent,
    DoneEvent,
    ErrorEvent,
    StatusEvent,
    TokenEvent,
)
from app.agent.prompts import build_system_prompt
from app.agent.providers import resolve_provider
from app.agent.tools import TOOL_DEFINITIONS, execute_tool
from app.config import Settings
from app.errors import AppError
from app.repos import MessageRepo, SessionRepo
from app.retrieval.embedder import OllamaEmbedder
from app.retrieval.search import hybrid_search

logger = structlog.get_logger(__name__)


class AgentService:
    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings
        self.embedder = OllamaEmbedder(host=settings.ollama_host, model=settings.embed_model)
        self.session_repo = SessionRepo(db)
        self.message_repo = MessageRepo(db)

    async def stream_turn(
        self,
        session_id: uuid.UUID,
        user_prompt: str,
    ) -> AsyncGenerator[str, None]:
        start_time = time.time()
        citations_recorded: List[dict[str, Any]] = []
        full_assistant_text: List[str] = []

        session = await self.session_repo.get(session_id)
        if not session:
            yield ErrorEvent(code="not_found", message=f"Session {session_id} not found").to_sse()
            return

        # 1. Record user message in DB
        await self.message_repo.add(session_id=session_id, role="user", content=user_prompt)
        await self.db.commit()

        # Update session touch
        await self.session_repo.touch(session_id)
        await self.db.commit()

        # 2. Resolve provider & model
        try:
            resolved = resolve_provider(self.settings, session.provider, session.model)
        except AppError as exc:
            yield ErrorEvent(code=exc.code, message=exc.message, detail=exc.detail).to_sse()
            return

        # 3. Handle Degraded/Stuffed Mode (pre-retrieval without tool roundtrips)
        if self.settings.agent_mode == "stuffed":
            yield StatusEvent(message="Searching transcripts (stuffed mode)...").to_sse()
            chunks = await hybrid_search(self.db, self.embedder, user_prompt, top_k=6)
            for c in chunks:
                citations_recorded.append(c.to_dict())
                yield CitationEvent(
                    chunk_id=c.chunk_id,
                    guest=c.guest,
                    title=c.title,
                    episode_slug=c.episode_slug,
                    start_ts=c.start_ts,
                    youtube_url=c.youtube_url,
                    snippet=c.text[:200],
                ).to_sse()

            if not chunks:
                refusal = "The transcripts of Lenny's Podcast don't appear to cover this topic."
                yield TokenEvent(text=refusal).to_sse()
                msg = await self.message_repo.add(
                    session_id=session_id,
                    role="assistant",
                    content=refusal,
                    citations=[],
                    stats={"stuffed": True, "duration_s": round(time.time() - start_time, 2)},
                )
                await self.db.commit()
                yield DoneEvent(message_id=msg.id, stats={"duration_s": round(time.time() - start_time, 2)}).to_sse()
                return

            # Build stuffed context prompt
            context_block = "\n\n---\n\n".join(
                f"Guest: {c.guest}\nTitle: {c.title}\nTimestamp: {c.start_ts}s\nURL: {c.youtube_url}\nExcerpt: {c.text}"
                for c in chunks
            )
            stuffed_user_prompt = f"Transcript Evidence:\n{context_block}\n\nUser Question:\n{user_prompt}"
            # Stream with context attached
            async for evt in self._stream_direct_completion(
                resolved, session_id, stuffed_user_prompt, citations_recorded, start_time
            ):
                yield evt
            return

        # 4. Standard Agentic Loop with Tool Calling
        # Fetch conversation history
        prior_messages = await self.message_repo.for_session(session_id)
        # Format messages for OpenAI / Ollama chat format
        api_messages: List[dict[str, Any]] = [
            {"role": "system", "content": build_system_prompt()}
        ]
        for m in prior_messages:
            api_messages.append({"role": m.role, "content": m.content})

        async with httpx.AsyncClient(timeout=float(self.settings.model_timeout_s)) as client:
            turns = 0
            while turns < self.settings.max_turns:
                turns += 1
                payload = {
                    "model": resolved.model,
                    "messages": api_messages,
                    "tools": TOOL_DEFINITIONS,
                    "stream": True,
                }

                try:
                    resp = await client.post(
                        f"{resolved.base_url}/chat/completions",
                        json=payload,
                        headers=resolved.headers,
                    )
                except Exception as exc:
                    logger.error("llm_connection_failed", provider=resolved.provider, error=str(exc))
                    yield ErrorEvent(
                        code="provider_unavailable",
                        message=f"Failed to communicate with provider '{resolved.provider}'",
                        detail={"provider": resolved.provider, "error": str(exc)},
                    ).to_sse()
                    return

                if resp.status_code != 200:
                    error_text = await resp.aread()
                    yield ErrorEvent(
                        code="provider_error",
                        message=f"Provider '{resolved.provider}' returned HTTP {resp.status_code}",
                        detail={"error": error_text.decode("utf-8", errors="ignore")},
                    ).to_sse()
                    return

                current_turn_text = ""
                tool_calls_accumulator: dict[int, dict[str, Any]] = {}

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})

                    # Text delta
                    if "content" in delta and delta["content"]:
                        token = delta["content"]
                        current_turn_text += token
                        full_assistant_text.append(token)
                        yield TokenEvent(text=token).to_sse()

                    # Tool call deltas
                    if "tool_calls" in delta and delta["tool_calls"]:
                        for tc in delta["tool_calls"]:
                            idx = tc.get("index", 0)
                            if idx not in tool_calls_accumulator:
                                tool_calls_accumulator[idx] = {
                                    "id": tc.get("id", f"call_{uuid.uuid4().hex[:8]}"),
                                    "name": "",
                                    "arguments": "",
                                }
                            if "function" in tc:
                                fn = tc["function"]
                                if "name" in fn and fn["name"]:
                                    tool_calls_accumulator[idx]["name"] += fn["name"]
                                if "arguments" in fn and fn["arguments"]:
                                    tool_calls_accumulator[idx]["arguments"] += fn["arguments"]

                # If no tool calls made, agent response is complete!
                if not tool_calls_accumulator:
                    break

                # Otherwise, execute requested tools
                api_messages.append({
                    "role": "assistant",
                    "content": current_turn_text or None,
                    "tool_calls": [
                        {
                            "id": t["id"],
                            "type": "function",
                            "function": {"name": t["name"], "arguments": t["arguments"]},
                        }
                        for t in tool_calls_accumulator.values()
                    ],
                })

                for tc in tool_calls_accumulator.values():
                    fn_name = tc["name"]
                    try:
                        args = json.loads(tc["arguments"])
                    except json.JSONDecodeError:
                        args = {}

                    # Notify status
                    if fn_name == "search_transcripts":
                        q = args.get("query", "topic")
                        yield StatusEvent(message=f"Searching transcripts for '{q}'...").to_sse()
                    elif fn_name == "get_episode_context":
                        ep = args.get("episode_slug", "episode")
                        yield StatusEvent(message=f"Reading context from {ep}...").to_sse()
                    elif fn_name in ("create_artifact", "update_artifact"):
                        title = args.get("title", "artifact")
                        yield StatusEvent(message=f"Generating artifact '{title}'...").to_sse()

                    async def on_artifact_created(payload: dict[str, Any]):
                        yield ArtifactEvent(
                            id=payload["id"],
                            group_id=payload["group_id"],
                            version=payload["version"],
                            kind=payload["kind"],
                            title=payload["title"],
                            content=payload["content"],
                            change_note=payload.get("change_note"),
                        ).to_sse()

                    result_payload = await execute_tool(
                        name=fn_name,
                        arguments=args,
                        db=self.db,
                        embedder=self.embedder,
                        session_id=session_id,
                        artifact_callback=on_artifact_created,
                    )

                    # If search returned results, emit citation events
                    if fn_name == "search_transcripts" and result_payload.get("status") == "success":
                        for c in result_payload.get("results", []):
                            citations_recorded.append(c)
                            yield CitationEvent(
                                chunk_id=c["chunk_id"],
                                guest=c["guest"],
                                title=c["title"],
                                episode_slug=c["episode_slug"],
                                start_ts=c["start_ts"],
                                youtube_url=c["youtube_url"],
                                snippet=c["text"][:200],
                            ).to_sse()

                    api_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": fn_name,
                        "content": json.dumps(result_payload),
                    })

        # Save assistant message in DB
        assistant_content = "".join(full_assistant_text)
        stats = {
            "provider": session.provider,
            "model": session.model,
            "duration_s": round(time.time() - start_time, 2),
            "citations_count": len(citations_recorded),
        }
        msg = await self.message_repo.add(
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            citations=citations_recorded,
            stats=stats,
        )
        await self.db.commit()

        yield DoneEvent(message_id=msg.id, stats=stats).to_sse()

    async def _stream_direct_completion(
        self,
        resolved: Any,
        session_id: uuid.UUID,
        user_prompt: str,
        citations: List[dict[str, Any]],
        start_time: float,
    ) -> AsyncGenerator[str, None]:
        full_text: List[str] = []
        messages = [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": user_prompt},
        ]
        async with httpx.AsyncClient(timeout=float(self.settings.model_timeout_s)) as client:
            resp = await client.post(
                f"{resolved.base_url}/chat/completions",
                json={"model": resolved.model, "messages": messages, "stream": True},
                headers=resolved.headers,
            )
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                d = line[6:].strip()
                if d == "[DONE]":
                    break
                try:
                    c = json.loads(d)
                    token = c.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if token:
                        full_text.append(token)
                        yield TokenEvent(text=token).to_sse()
                except Exception:
                    continue

        content = "".join(full_text)
        stats = {"stuffed": True, "duration_s": round(time.time() - start_time, 2)}
        msg = await self.message_repo.add(
            session_id=session_id,
            role="assistant",
            content=content,
            citations=citations,
            stats=stats,
        )
        await self.db.commit()
        yield DoneEvent(message_id=msg.id, stats=stats).to_sse()
