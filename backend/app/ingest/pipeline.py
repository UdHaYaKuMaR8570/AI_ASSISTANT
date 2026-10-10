import asyncio
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db import get_engine, get_sessionmaker
from app.ingest.chunker import chunk_turns
from app.ingest.parser import parse_transcript
from app.repos import ChunkRepo
from app.retrieval.embedder import OllamaEmbedder

logger = structlog.get_logger(__name__)


@dataclass
class IngestStats:
    episodes: int = 0
    chunks: int = 0
    skipped: int = 0
    elapsed_seconds: float = 0.0


async def ingest_file(
    path: Path,
    db: AsyncSession,
    embedder: OllamaEmbedder,
    repo: ChunkRepo,
) -> int:
    """Ingests a single transcript file, chunking, embedding, and inserting into DB."""
    text = path.read_text(encoding="utf-8")
    parsed = parse_transcript(text)
    meta = parsed.meta

    # Ensure slug exists
    slug = meta.get("slug") or path.stem
    meta["slug"] = slug

    episode_id = await repo.upsert_episode(meta)
    drafts = chunk_turns(parsed.turns)
    if not drafts:
        return 0

    # Embed draft texts
    texts_to_embed = [d.text for d in drafts]
    embeddings = await embedder.embed(texts_to_embed, doc=True)

    chunk_dicts = []
    for i, draft in enumerate(drafts):
        chunk_dicts.append(
            {
                "chunk_index": draft.chunk_index,
                "text": draft.text,
                "token_count": draft.token_count,
                "start_ts": draft.start_ts,
                "speaker": draft.speaker,
                "embedding": embeddings[i] if i < len(embeddings) else None,
                "content_hash": draft.content_hash,
            }
        )

    inserted = await repo.upsert_chunks(episode_id, chunk_dicts)
    await db.commit()
    return inserted


async def run_ingest(settings: Settings, *, limit: Optional[int] = None) -> IngestStats:
    start_time = time.time()
    stats = IngestStats()
    corpus_path = Path(settings.corpus_dir)

    # If corpus directory doesn't exist, check for clone
    if not corpus_path.exists() or not any(corpus_path.glob("*.md")):
        logger.info("corpus_directory_empty_or_missing", path=str(corpus_path))
        corpus_path.mkdir(parents=True, exist_ok=True)
        try:
            logger.info("attempting_corpus_git_clone")
            subprocess.run(
                ["git", "clone", "--depth", "1", "https://github.com/ChatPRD/lennys-podcast-transcripts.git", str(corpus_path)],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except Exception as exc:
            logger.warning("corpus_clone_skipped_or_failed", error=str(exc))

    md_files = sorted(list(corpus_path.glob("*.md")))
    if limit:
        md_files = md_files[:limit]

    logger.info("ingest_starting", total_files=len(md_files))

    embedder = OllamaEmbedder(host=settings.ollama_host, model=settings.embed_model)
    session_factory = get_sessionmaker()

    for path in md_files:
        try:
            async with session_factory() as db:
                repo = ChunkRepo(db)
                inserted = await ingest_file(path, db, embedder, repo)
                stats.episodes += 1
                stats.chunks += inserted
                logger.info("file_ingested", file=path.name, chunks=inserted)
        except Exception as exc:
            stats.skipped += 1
            logger.warning("file_ingest_failed", file=path.name, error=str(exc))

    stats.elapsed_seconds = round(time.time() - start_time, 2)
    logger.info("ingest_completed", episodes=stats.episodes, chunks=stats.chunks, elapsed_s=stats.elapsed_seconds)
    return stats


if __name__ == "__main__":
    from app.config import get_settings
    settings = get_settings()
    asyncio.run(run_ingest(settings, limit=settings.ingest_limit))
