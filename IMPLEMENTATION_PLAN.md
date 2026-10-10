# The Lenny Growth Assistant — Implementation Plan & Status Tracker

**Repository:** `d:\AI Assit`  
**Goal:** Build and verify a grounded conversational RAG assistant over Lenny's Podcast transcripts with session/message persistence, local Ollama + cloud LLM routing, Ship 30 essay skill, sandboxed artifact viewer (MD/HTML), and Docker Compose.

---

## Priorities & Verification Status

### 1. Functioning React Frontend Connected to FastAPI
- [x] React 18 + TypeScript + Vite + Tailwind CSS + Lucide icons SPA structure
- [x] REST API client with SSE streaming support (`POST /api/sessions/{id}/messages`)
- [x] Real-time token streaming, tool call status narration, and interactive citation chips
- [x] Session management (create, list, select, soft-delete, new-chat modal)
- [x] Full production build tested and verified (`vite build` succeeded: 229 kB bundle)

### 2. PostgreSQL Session and Message Persistence
- [x] PostgreSQL 17 + `pgvector` schema (`episodes`, `chunks`, `sessions`, `messages`, `artifacts`)
- [x] SQLAlchemy async engine + `asyncpg` with transaction safety, pooling, and `apply_schema` initialization
- [x] Session repository: create, list, retrieve, soft-delete, metadata tracking
- [x] Message repository: persist turns, citations JSONB, execution stats
- [x] Artifact repository: versioning (v1, v2...), artifact group tracking

### 3. Ollama Local-Model Integration
- [x] Local Ollama provider configuration (`nomic-embed-text` embeddings + `qwen3:4b` inference)
- [x] Zero-key local execution path
- [x] LiteLLM gateway configuration routing Anthropic-format messages to local Ollama
- [x] Degraded local mode handling (`AGENT_MODE=stuffed` prompt-stuffing fallback)

### 4. Transcript Ingestion, RAG Retrieval & Source Attribution
- [x] Transcript parser with frontmatter metadata and speaker turn extraction (`test_parser.py` passing)
- [x] Speaker-turn chunker with token limits, sentence boundary splitting, and overlap (`test_chunker.py` passing)
- [x] Vector search with cosine distance over pgvector + full-text search (`tsvector`) + Reciprocal Rank Fusion (RRF)
- [x] Relevance floor gating (`RELEVANCE_FLOOR = 0.010`) to guarantee honest refusal when ungrounded
- [x] Exact YouTube timestamp deep-links and verified citation chips

### 5. Dedicated Essay-Writing Skill
- [x] Ship 30 for 30 essay writing skill (`backend/skills/ship30-essay/SKILL.md`)
- [x] Proven frameworks (Headline formula, 1-3-1 rhythm, atomic essays, ~250–350 words)
- [x] System prompt injection and quick-action trigger ("✍️ Ship 30 essay")

### 6. Safe Markdown & HTML/CSS Artifact Generation & Preview
- [x] Versioned artifact panel (split view / drawer) with version stepper (`v1` ◂ ▸ `v2`)
- [x] Self-contained Markdown renderer with editorial typography and code formatting
- [x] Sandboxed iframe for HTML/CSS previews (`sandbox="allow-scripts"` without `allow-same-origin`)
- [x] Source view toggle and download export capability (`.md` and `.html`)
- [x] Zero-dependency HTML sanitizer stripping scripts and dangerous inline event handlers

### 7. Cloud Provider Configuration
- [x] Unified provider toggle: `ollama`, `anthropic`, `openai`, `custom` (OpenRouter/vLLM)
- [x] LiteLLM configuration for OpenAI & custom OpenAI-compatible endpoints
- [x] Health check endpoint (`GET /api/health`) reporting per-provider readiness (`test_health.py` passing)
- [x] Env validation and graceful error envelopes (`{"error": {"code": ...}}`)

### 8. Tests, Docker Compose & Documentation
- [x] `deploy/docker-compose.yml` multi-service stack (db, litellm, api, web, ingest)
- [x] Automated test suite: 13 backend pytest unit/integration tests passing
- [x] Complete documentation: `README.md`, `.env.example`, `Makefile`
- [x] Clean production build verified
