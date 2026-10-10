import React from 'react';
import { MessageSquarePlus, Trash2 } from 'lucide-react';
import { useAppStore } from '../state/store';
import { HealthDot } from './HealthDot';

export const Sidebar: React.FC = () => {
  const {
    sessions,
    activeSessionId,
    selectSession,
    deleteCurrentSession,
    setNewChatModalOpen,
  } = useAppStore();

  return (
    <aside className="w-64 sm:w-72 flex-shrink-0 h-full bg-paper-100 border-r border-paper-300 flex flex-col justify-between select-none">
      {/* Top Header & New Chat */}
      <div className="p-4 border-b border-paper-200">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-7 h-7 rounded-lg bg-coral-500 flex items-center justify-center text-white font-serif font-bold text-sm shadow-xs">
            L
          </div>
          <div>
            <h1 className="font-serif font-bold text-sm text-ink leading-tight">
              Lenny Growth
            </h1>
            <p className="text-[10px] text-ink-muted">AI Podcast Assistant</p>
          </div>
        </div>

        <button
          onClick={() => setNewChatModalOpen(true)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-coral-500 hover:bg-coral-600 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
        >
          <MessageSquarePlus className="w-4 h-4" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.map((s) => {
          const isActive = s.id === activeSessionId;
          return (
            <div
              key={s.id}
              onClick={() => selectSession(s.id)}
              className={`group flex items-center justify-between px-3 py-2 rounded-lg text-xs cursor-pointer transition-colors ${
                isActive
                  ? 'bg-paper-200 text-ink font-semibold shadow-2xs'
                  : 'text-ink-muted hover:bg-paper-200/50 hover:text-ink'
              }`}
            >
              <div className="truncate mr-2">
                <p className="truncate">{s.title || 'Conversation'}</p>
                <p className="text-[10px] text-ink-faint capitalize font-mono">
                  {s.provider}
                </p>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteCurrentSession(s.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-500 rounded transition-opacity"
                title="Delete session"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}

        {sessions.length === 0 && (
          <div className="p-4 text-center text-xs text-ink-muted italic">
            No conversations yet.
          </div>
        )}
      </div>

      {/* Footer Info & Health */}
      <div className="p-4 border-t border-paper-200 bg-paper-100/50 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <HealthDot />
          <span className="text-[10px] font-mono text-ink-faint">v0.1.0</span>
        </div>
        <p className="text-[10px] text-ink-faint">
          301 episodes • Grounded RAG
        </p>
      </div>
    </aside>
  );
};
