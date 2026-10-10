import { AppConfig, Artifact, HealthStatus, Session } from './types';

export function getAnonymousUserId(): string {
  const key = 'lenny_user_id';
  let id = localStorage.getItem(key);
  if (!id) {
    id = 'user_' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem(key, id);
  }
  return id;
}

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health probe failed');
  return res.json();
}

export async function fetchConfig(): Promise<AppConfig> {
  const res = await fetch(`${API_BASE}/config`);
  if (!res.ok) throw new Error('Config load failed');
  return res.json();
}

export async function fetchSessions(userId: string): Promise<Session[]> {
  const res = await fetch(`${API_BASE}/sessions?user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error('Failed to load sessions');
  return res.json();
}

export async function createSession(data: {
  user_id: string;
  provider: string;
  model: string;
  title: string;
}): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || 'Failed to create session');
  }
  return res.json();
}

export async function fetchSessionDetails(sessionId: string): Promise<{
  session: Session;
  messages: any[];
  artifacts: Artifact[];
}> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
  if (!res.ok) throw new Error('Failed to load session details');
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete session');
}

export interface StreamHandlers {
  onToken?: (text: string) => void;
  onStatus?: (message: string) => void;
  onCitation?: (citation: any) => void;
  onArtifact?: (artifact: any) => void;
  onDone?: (data: { message_id: number; stats: any }) => void;
  onError?: (error: { code: string; message: string; detail?: any }) => void;
}

export async function streamMessage(
  sessionId: string,
  content: string,
  handlers: StreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
    signal,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `HTTP ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error('No readable response body');

  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const chunk of lines) {
      const parts = chunk.split('\n');
      let eventType = 'message';
      let dataText = '';

      for (const line of parts) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          dataText = line.slice(6).trim();
        }
      }

      if (!dataText) continue;

      try {
        const parsed = JSON.parse(dataText);
        if (eventType === 'token') {
          handlers.onToken?.(parsed.text);
        } else if (eventType === 'status') {
          handlers.onStatus?.(parsed.message);
        } else if (eventType === 'citation') {
          handlers.onCitation?.(parsed);
        } else if (eventType === 'artifact') {
          handlers.onArtifact?.(parsed);
        } else if (eventType === 'done') {
          handlers.onDone?.(parsed);
        } else if (eventType === 'error') {
          handlers.onError?.(parsed.error);
        }
      } catch (err) {
        console.error('Failed to parse SSE event chunk:', err);
      }
    }
  }
}
