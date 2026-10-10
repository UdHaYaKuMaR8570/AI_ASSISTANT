from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Runtime configuration read from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Provider selection: ollama | anthropic | openai | custom
    llm_provider: str = "ollama"

    # Cloud providers
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-5"

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    custom_base_url: Optional[str] = None
    custom_api_key: Optional[str] = None
    custom_model: Optional[str] = None

    # Local Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    embed_model: str = "nomic-embed-text"

    # Database & Gateway
    database_url: str = "postgresql+asyncpg://lenny:lenny@localhost:5433/lenny"
    litellm_url: str = "http://localhost:4000"
    litellm_master_key: str = "sk-litellm-local"

    # Agent runtime controls
    model_timeout_s: int = 120
    agent_mode: str = "agentic"  # "agentic" | "stuffed"
    max_turns: int = 8

    # Ingestion controls
    ingest_limit: Optional[int] = None
    corpus_dir: str = "./corpus"


@lru_cache
def get_settings() -> Settings:
    return Settings()
