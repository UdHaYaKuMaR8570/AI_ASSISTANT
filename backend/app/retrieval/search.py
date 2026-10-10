from dataclasses import dataclass
from typing import Any, List, Optional

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.embedder import OllamaEmbedder

logger = structlog.get_logger(__name__)

RELEVANCE_FLOOR = 0.010  # RRF score cutoff for honest refusal


@dataclass
class RetrievedChunk:
    chunk_id: int
    episode_slug: str
    guest: str
    title: str
    speaker: str
    start_ts: int
    youtube_url: str
    text: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "episode_slug": self.episode_slug,
            "guest": self.guest,
            "title": self.title,
            "speaker": self.speaker,
            "start_ts": self.start_ts,
            "youtube_url": self.youtube_url,
            "text": self.text,
            "score": round(self.score, 4),
        }


def format_youtube_timestamp_url(base_url: Optional[str], start_ts: Optional[int]) -> str:
    if not base_url:
        return ""
    if start_ts is None or start_ts <= 0:
        return base_url
    delimiter = "&" if "?" in base_url else "?"
    return f"{base_url}{delimiter}t={start_ts}s"


async def hybrid_search(
    db: AsyncSession,
    embedder: OllamaEmbedder,
    query: str,
    top_k: int = 6,
) -> List[RetrievedChunk]:
    """Performs hybrid retrieval using pgvector cosine search and full-text search, fused with RRF."""
    # 1. Generate query embedding
    query_vector: Optional[List[float]] = None
    try:
        vecs = await embedder.embed([query], doc=False)
        if vecs:
            query_vector = vecs[0]
    except Exception as exc:
        logger.warning("query_embedding_fallback", error=str(exc))

    # Clean query for FTS plainto_tsquery
    clean_fts_query = query.strip()

    # SQL query executing hybrid search + Reciprocal Rank Fusion (k=60)
    # If query_vector is absent, fallback gracefully to FTS only
    if query_vector:
        sql = text("""
            WITH vector_matches AS (
                SELECT c.id, c.episode_id, c.chunk_index, c.text, c.start_ts, c.speaker,
                       ROW_NUMBER() OVER (ORDER BY c.embedding <=> cast(:vec as vector)) AS r_vec
                FROM chunks c
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> cast(:vec as vector)
                LIMIT 40
            ),
            fts_matches AS (
                SELECT c.id, c.episode_id, c.chunk_index, c.text, c.start_ts, c.speaker,
                       ROW_NUMBER() OVER (ORDER BY ts_rank_cd(c.tsv, plainto_tsquery('english', :fts_query)) DESC) AS r_fts
                FROM chunks c
                WHERE c.tsv @@ plainto_tsquery('english', :fts_query)
                ORDER BY ts_rank_cd(c.tsv, plainto_tsquery('english', :fts_query)) DESC
                LIMIT 40
            ),
            fused AS (
                SELECT COALESCE(v.id, f.id) AS id,
                       COALESCE(v.episode_id, f.episode_id) AS episode_id,
                       COALESCE(v.chunk_index, f.chunk_index) AS chunk_index,
                       COALESCE(v.text, f.text) AS text,
                       COALESCE(v.start_ts, f.start_ts) AS start_ts,
                       COALESCE(v.speaker, f.speaker) AS speaker,
                       (COALESCE(1.0 / (60.0 + v.r_vec), 0.0) + COALESCE(1.0 / (60.0 + f.r_fts), 0.0)) AS score
                FROM vector_matches v
                FULL OUTER JOIN fts_matches f ON v.id = f.id
            )
            SELECT f.id, f.episode_id, f.chunk_index, f.text, f.start_ts, f.speaker, f.score,
                   e.slug, e.guest, e.title, e.youtube_url
            FROM fused f
            JOIN episodes e ON f.episode_id = e.id
            ORDER BY f.score DESC
            LIMIT :top_k;
        """)
        params = {
            "vec": str(query_vector),
            "fts_query": clean_fts_query,
            "top_k": top_k,
        }
    else:
        sql = text("""
            WITH fts_matches AS (
                SELECT c.id, c.episode_id, c.chunk_index, c.text, c.start_ts, c.speaker,
                       ROW_NUMBER() OVER (ORDER BY ts_rank_cd(c.tsv, plainto_tsquery('english', :fts_query)) DESC) AS r_fts
                FROM chunks c
                WHERE c.tsv @@ plainto_tsquery('english', :fts_query)
                ORDER BY ts_rank_cd(c.tsv, plainto_tsquery('english', :fts_query)) DESC
                LIMIT :top_k
            )
            SELECT f.id, f.episode_id, f.chunk_index, f.text, f.start_ts, f.speaker,
                   (1.0 / (60.0 + f.r_fts)) AS score,
                   e.slug, e.guest, e.title, e.youtube_url
            FROM fts_matches f
            JOIN episodes e ON f.episode_id = e.id
            ORDER BY score DESC;
        """)
        params = {
            "fts_query": clean_fts_query,
            "top_k": top_k,
        }

    res = await db.execute(sql, params)
    rows = res.fetchall()

    chunks: List[RetrievedChunk] = []
    for r in rows:
        score = float(r.score)
        # Relevance floor check
        if score < RELEVANCE_FLOOR:
            continue
        yt_url = format_youtube_timestamp_url(r.youtube_url, r.start_ts)
        chunks.append(
            RetrievedChunk(
                chunk_id=r.id,
                episode_slug=r.slug,
                guest=r.guest or "Unknown Guest",
                title=r.title or "Lenny's Podcast",
                speaker=r.speaker or "Guest",
                start_ts=r.start_ts or 0,
                youtube_url=yt_url,
                text=r.text,
                score=score,
            )
        )

    logger.info("retrieval_completed", query=query, retrieved_count=len(chunks))
    return chunks
