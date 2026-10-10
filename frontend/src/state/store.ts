import { create } from 'zustand';
import {
  createSession,
  deleteSession,
  fetchConfig,
  fetchHealth,
  fetchSessionDetails,
  fetchSessions,
  getAnonymousUserId,
  streamMessage,
} from '../api/client';
import { AppConfig, Artifact, HealthStatus, Message, Session } from '../api/types';

interface AppState {
  userId: string;
  sessions: Session[];
  activeSessionId: string | null;
  messages: Message[];
  artifacts: Artifact[];
  health: HealthStatus | null;
  config: AppConfig | null;

  isStreaming: boolean;
  statusMessage: string | null;
  isNewChatModalOpen: boolean;
  isArtifactPanelOpen: boolean;
  activeArtifactGroupId: string | null;

  // Actions
  init: () => Promise<void>;
  selectSession: (sessionId: string) => Promise<void>;
  startNewSession: (provider: string, model: string, title?: string) => Promise<string>;
  deleteCurrentSession: (sessionId: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  setNewChatModalOpen: (open: boolean) => void;
  setArtifactPanelOpen: (open: boolean) => void;
  setActiveArtifactGroupId: (groupId: string | null) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  userId: getAnonymousUserId(),
  sessions: [],
  activeSessionId: null,
  messages: [],
  artifacts: [],
  health: null,
  config: null,

  isStreaming: false,
  statusMessage: null,
  isNewChatModalOpen: false,
  isArtifactPanelOpen: false,
  activeArtifactGroupId: null,

  init: async () => {
    const userId = get().userId;
    try {
      const [health, config, sessions] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchConfig().catch(() => null),
        fetchSessions(userId).catch(() => []),
      ]);

      set({ health, config, sessions });

      if (sessions.length > 0) {
        await get().selectSession(sessions[0].id);
      }
    } catch (err) {
      console.error('Initialization error:', err);
    }
  },

  selectSession: async (sessionId: string) => {
    try {
      set({ activeSessionId: sessionId, messages: [], statusMessage: null });
      const details = await fetchSessionDetails(sessionId);
      set({
        messages: details.messages,
        artifacts: details.artifacts,
        activeArtifactGroupId: details.artifacts.length > 0 ? details.artifacts[0].group_id : null,
        isArtifactPanelOpen: details.artifacts.length > 0,
      });
    } catch (err) {
      console.error('Failed to switch session:', err);
    }
  },

  startNewSession: async (provider: string, model: string, title: string = 'New Conversation') => {
    const userId = get().userId;
    const session = await createSession({
      user_id: userId,
      provider,
      model,
      title,
    });

    const sessions = [session, ...get().sessions];
    set({
      sessions,
      activeSessionId: session.id,
      messages: [],
      artifacts: [],
      isNewChatModalOpen: false,
      isArtifactPanelOpen: false,
    });
    return session.id;
  },

  deleteCurrentSession: async (sessionId: string) => {
    await deleteSession(sessionId);
    const updated = get().sessions.filter((s) => s.id !== sessionId);
    set({ sessions: updated });

    if (get().activeSessionId === sessionId) {
      if (updated.length > 0) {
        await get().selectSession(updated[0].id);
      } else {
        set({ activeSessionId: null, messages: [], artifacts: [] });
      }
    }
  },

  sendMessage: async (text: string) => {
    let sessionId = get().activeSessionId;
    const config = get().config;

    // If no active session, auto-create one with defaults
    if (!sessionId) {
      const defaultProv = config?.default_provider || 'ollama';
      const defaultMod = config?.default_model?.[defaultProv] || 'qwen3:4b';
      sessionId = await get().startNewSession(defaultProv, defaultMod, text.slice(0, 32));
    }

    // Add optimistic user message
    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: text,
      citations: [],
      created_at: new Date().toISOString(),
    };

    // Placeholder assistant message
    const assistantId = Date.now() + 1;
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      citations: [],
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg, assistantMsg],
      isStreaming: true,
      statusMessage: 'Thinking...',
    }));

    try {
      await streamMessage(sessionId, text, {
        onToken: (token) => {
          set((state) => {
            const msgs = [...state.messages];
            const last = msgs[msgs.length - 1];
            if (last && last.role === 'assistant') {
              last.content += token;
            }
            return { messages: msgs };
          });
        },
        onStatus: (msg) => {
          set({ statusMessage: msg });
        },
        onCitation: (cit) => {
          set((state) => {
            const msgs = [...state.messages];
            const last = msgs[msgs.length - 1];
            if (last && last.role === 'assistant') {
              if (!last.citations.some((c) => c.chunk_id === cit.chunk_id)) {
                last.citations.push(cit);
              }
            }
            return { messages: msgs };
          });
        },
        onArtifact: (art) => {
          set((state) => {
            const existingIdx = state.artifacts.findIndex(
              (a) => a.group_id === art.group_id && a.version === art.version
            );
            const updated = [...state.artifacts];
            if (existingIdx >= 0) {
              updated[existingIdx] = art;
            } else {
              updated.unshift(art);
            }
            return {
              artifacts: updated,
              isArtifactPanelOpen: true,
              activeArtifactGroupId: art.group_id,
            };
          });
        },
        onDone: () => {
          set({ isStreaming: false, statusMessage: null });
        },
        onError: (err) => {
          set((state) => {
            const msgs = [...state.messages];
            const last = msgs[msgs.length - 1];
            if (last && last.role === 'assistant' && !last.content) {
              last.content = `Error: ${err.message}`;
            }
            return { messages: msgs, isStreaming: false, statusMessage: null };
          });
        },
      });
    } catch (err: any) {
      set((state) => {
        const msgs = [...state.messages];
        const last = msgs[msgs.length - 1];
        if (last && last.role === 'assistant' && !last.content) {
          last.content = `Connection Error: ${err.message}`;
        }
        return { messages: msgs, isStreaming: false, statusMessage: null };
      });
    }
  },

  setNewChatModalOpen: (open: boolean) => set({ isNewChatModalOpen: open }),
  setArtifactPanelOpen: (open: boolean) => set({ isArtifactPanelOpen: open }),
  setActiveArtifactGroupId: (groupId: string | null) => set({ activeArtifactGroupId: groupId }),
}));
