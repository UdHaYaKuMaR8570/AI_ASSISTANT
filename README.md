# The Lenny Growth Assistant

A grounded conversational AI advisor over **300+ episodes of Lenny's Podcast** (~16,000 indexed passages). Ask it any product management or startup growth question, and it answers strictly from what guests actually said on the podcast — with verifiable citations linking directly to the exact second on YouTube. If the corpus doesn't cover a topic, it provides an honest refusal instead of fabricating an answer.

It also writes: a dedicated **Ship 30 for 30 essay skill** turns any product insight into a structured atomic essay, and any response can be converted into a **versioned artifact** (Markdown or sandboxed HTML/CSS) rendered in an interactive side viewer.

---

## Architecture Overview

```
                      ┌─────────────────────────── Docker Compose ───────────────────────────┐
                      │                                                                       │
Browser ─────────────▶│  web (Nginx)              api (FastAPI + Agent Loop)                  │
  SPA (Vite/React)    │   ├─ Serves UI      ──▶    ├─ REST + SSE streaming                     │
                      │   └─ Proxies /api          ├─ Agent Tools                              │
                      │                            │   ├─ search_transcripts (RAG hybrid RRF)  │
                      │                            │   ├─ get_episode_context (temporal window)│
                      │                            │   └─ create/update_artifact (Postgres)    │
                      │                            ├─ Persistence (SQLAlchemy asyncpg)        │
                      │                            └─ Ingestion pipeline                       │
                      │                                 │                                     │
                      │  db (PostgreSQL 17 + pgvector) ◀┘     litellm (Gateway)               │
                      │   sessions/messages/artifacts/         ├─ openai/gpt-4o-mini          │
                      │   chunks/episodes                      ├─ openrouter / custom         │
                      │                                        └─ ollama_chat/qwen3:4b        │
                      └───────────────────────────────────────────────────────────────┬───────┘
                                                                                      ▼
                                                                  Host Ollama (Zero-key local LLM)
                                                                  qwen3:4b + nomic-embed-text
```

### Key Capabilities
1. **Grounded Conversational RAG**: Hybrid search fusing pgvector cosine distance + full-text search (`tsvector`) via Reciprocal Rank Fusion (RRF), gated by a relevance floor to guarantee honest refusal when ungrounded.
2. **True Source Attribution**: Inline citations `[Guest Name — Episode Title, HH:MM:SS]` that render as interactive chips deep-linking to YouTube timestamps.
3. **Dedicated Essay Skill**: Ship 30 for 30 framework for generating punchy, atomic essays (~250–350 words) with headline formulas, 1-3-1 rhythm, and practical takeaways.
4. **Sandboxed Artifact Viewer**: Slide-in panel rendering Markdown or sandboxed HTML (`sandbox="allow-scripts"` without `allow-same-origin`), with version steppers (`v1` ◂ ▸ `v2`), source view, and download exports.
5. **Multi-Provider Switcher**: Per-session provider selection across 4 modes:
   - **Local Ollama**: 100% private, zero API keys required (`qwen3:4b` + `nomic-embed-text`).
   - **Anthropic Claude**: `claude-sonnet-4-5` via API key.
   - **OpenAI**: `gpt-4o-mini` via LiteLLM gateway.
   - **Custom Endpoint**: OpenRouter, Together, vLLM, or any OpenAI-compatible provider.

---

## Quickstart

### 1. Environment Setup
Copy the sample environment file:
```bash
cp .env.example .env
```

### 2. Run with Docker Compose
To build and launch the entire stack (PostgreSQL + pgvector, LiteLLM gateway, FastAPI backend, and Nginx web app):
```bash
docker compose -f deploy/docker-compose.yml up -d --build
```
Once healthy, open **http://localhost:3000** in your browser.

To ingest transcripts:
```bash
docker compose -f deploy/docker-compose.yml run --rm ingest
```

---

## Local Development (Without Docker)

### Backend (FastAPI)
```bash
cd backend
uv venv
.\.venv\Scripts\activate
uv pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API endpoints will be active on **http://localhost:8000**.  
API docs available at **http://localhost:8000/docs**.

### Frontend (React + Vite)
```bash
cd frontend
npm run dev
```
Open **http://localhost:3000** (proxies `/api` to port 8000).

### Run Test Suites
```bash
# Backend pytest suite (unit + integration + parser + chunker + sessions)
cd backend
.\.venv\Scripts\python -m pytest

# Frontend production build verification
cd frontend
npx vite build
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | Default provider for new conversations (`ollama`, `anthropic`, `openai`, `custom`) | `ollama` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model for chat generation | `qwen3:4b` |
| `EMBED_MODEL` | Embedding model for vector retrieval | `nomic-embed-text` |
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://lenny:lenny@localhost:5433/lenny` |
| `LITELLM_URL` | LiteLLM gateway proxy endpoint | `http://localhost:4000` |
| `ANTHROPIC_API_KEY` | Optional key for Anthropic Claude | *(blank)* |
| `OPENAI_API_KEY` | Optional key for OpenAI | *(blank)* |
| `CUSTOM_BASE_URL` | Optional OpenAI-compatible base URL | *(blank)* |
| `CUSTOM_API_KEY` | Optional API key for custom endpoint | *(blank)* |
| `CUSTOM_MODEL` | Optional model name for custom endpoint | *(blank)* |
| `AGENT_MODE` | Runtime mode: `agentic` (tool calling) or `stuffed` (prompt stuffing fallback) | `agentic` |
