export interface Session {
  id: string;
  user_id: string;
  provider: 'ollama' | 'anthropic' | 'openai' | 'custom' | string;
  model: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  chunk_id: number;
  guest: string;
  title: string;
  episode_slug: string;
  start_ts: number;
  youtube_url: string;
  snippet?: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: Citation[];
  stats?: Record<string, any>;
  created_at: string;
}

export interface Artifact {
  id: number;
  group_id: string;
  version: number;
  kind: 'markdown' | 'html';
  title: string;
  content: string;
  change_note?: string;
  created_at: string;
}

export interface HealthStatus {
  status: 'ok' | 'degraded';
  checks: {
    db?: { status: string; detail?: string };
    ollama?: { status: string; models_loaded?: Record<string, boolean> };
    litellm?: { status: string };
    providers?: Record<string, boolean>;
  };
}

export interface ProviderOption {
  id: string;
  name: string;
  model: string;
  requires_key: boolean;
}

export interface AppConfig {
  default_provider: string;
  default_model: Record<string, string>;
  embed_model: string;
  agent_mode: string;
  available_providers: ProviderOption[];
}
