-- Lenny Growth Assistant schema (PostgreSQL 17 + pgvector)
-- Idempotent initialization: applied safely on application startup.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS episodes (
    id               bigserial PRIMARY KEY,
    slug             text NOT NULL UNIQUE,
    guest            text,
    title            text,
    youtube_url      text,
    video_id         text,
    publish_date     date,
    duration_seconds integer,
    keywords         text[],
    description      text,
    ingested_at      timestamptz NOT NULL DEFAULT clock_timestamp(),
    content_hash     text
);

CREATE TABLE IF NOT EXISTS chunks (
    id           bigserial PRIMARY KEY,
    episode_id   bigint NOT NULL REFERENCES episodes (id) ON DELETE CASCADE,
    chunk_index  integer NOT NULL,
    text         text NOT NULL,
    token_count  integer,
    start_ts     integer,           -- seconds offset in episode
    speaker      text,
    embedding    vector(768),       -- nomic-embed-text dimension
    content_hash text UNIQUE,
    tsv          tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);

CREATE INDEX IF NOT EXISTS idx_chunks_episode_id ON chunks (episode_id);
CREATE INDEX IF NOT EXISTS idx_chunks_tsv ON chunks USING gin (tsv);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS sessions (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        text NOT NULL,
    provider       text NOT NULL DEFAULT 'ollama',
    model          text NOT NULL DEFAULT 'qwen3:4b',
    title          text NOT NULL DEFAULT 'New Conversation',
    sdk_session_id text,
    created_at     timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at     timestamptz NOT NULL DEFAULT clock_timestamp(),
    deleted_at     timestamptz
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions (updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id         bigserial PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
    role       text NOT NULL, -- 'user' | 'assistant' | 'system'
    content    text NOT NULL,
    citations  jsonb NOT NULL DEFAULT '[]'::jsonb,
    stats      jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages (session_id, created_at ASC);

CREATE TABLE IF NOT EXISTS artifacts (
    id                bigserial PRIMARY KEY,
    artifact_group_id uuid NOT NULL DEFAULT gen_random_uuid(),
    session_id        uuid NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
    message_id        bigint REFERENCES messages (id) ON DELETE SET NULL,
    version           integer NOT NULL DEFAULT 1,
    kind              text NOT NULL DEFAULT 'markdown', -- 'markdown' | 'html'
    title             text NOT NULL,
    content           text NOT NULL,
    change_note       text,
    created_at        timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_artifacts_session ON artifacts (session_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_group ON artifacts (artifact_group_id, version ASC);
