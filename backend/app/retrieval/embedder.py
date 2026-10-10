from typing import List

import httpx
import structlog

from app.errors import AppError

logger = structlog.get_logger(__name__)


class OllamaEmbedder:
    """Generates embeddings via local Ollama nomic-embed-text endpoint."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.host = host.rstrip("/")
        self.model = model

    async def embed(self, texts: List[str], *, doc: bool = True) -> List[List[float]]:
        if not texts:
            return []

        prefix = "search_document: " if doc else "search_query: "
        prefixed_inputs = [f"{prefix}{t}" for t in texts]
        results: List[List[float]] = []
        batch_size = 32

        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(0, len(prefixed_inputs), batch_size):
                batch = prefixed_inputs[i : i + batch_size]
                try:
                    resp = await client.post(
                        f"{self.host}/api/embed",
                        json={"model": self.model, "input": batch},
                    )
                except Exception as exc:
                    logger.error("ollama_embed_connect_failed", error=str(exc))
                    raise AppError(
                        code="ollama_down",
                        message="Ollama embedding service is unreachable",
                        status_code=502,
                        detail={"host": self.host, "model": self.model, "error": str(exc)},
                    )

                if resp.status_code != 200:
                    raise AppError(
                        code="embed_error",
                        message=f"Ollama returned HTTP {resp.status_code}: {resp.text}",
                        status_code=502,
                    )

                data = resp.json()
                embeddings = data.get("embeddings") or []
                results.extend(embeddings)

        return results
