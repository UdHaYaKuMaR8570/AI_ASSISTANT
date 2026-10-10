import React, { useState } from 'react';
import { Cpu, Globe, Key, ShieldCheck, X } from 'lucide-react';
import { useAppStore } from '../state/store';

export const NewChatModal: React.FC = () => {
  const {
    isNewChatModalOpen,
    setNewChatModalOpen,
    startNewSession,
    config,
    health,
  } = useAppStore();

  const [selectedProvider, setSelectedProvider] = useState<string>(
    config?.default_provider || 'ollama'
  );

  if (!isNewChatModalOpen) return null;

  const providers = config?.available_providers || [
    { id: 'ollama', name: 'Local Ollama', model: 'qwen3:4b', requires_key: False },
    { id: 'anthropic', name: 'Anthropic Claude', model: 'claude-sonnet-4-5', requires_key: True },
    { id: 'openai', name: 'OpenAI', model: 'gpt-4o-mini', requires_key: True },
    { id: 'custom', name: 'Custom Endpoint', model: 'custom', requires_key: True },
  ];

  const handleStart = async () => {
    const prov = providers.find((p) => p.id === selectedProvider);
    if (!prov) return;
    await startNewSession(prov.id, prov.model);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-md bg-paper-50 rounded-2xl border border-paper-300 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-5 py-4 border-b border-paper-200 flex items-center justify-between bg-paper-100">
          <div>
            <h2 className="font-serif font-bold text-base text-ink">
              Start New Conversation
            </h2>
            <p className="text-xs text-ink-muted">
              Choose your LLM provider for this session
            </p>
          </div>
          <button
            onClick={() => setNewChatModalOpen(false)}
            className="p-1 text-ink-muted hover:text-ink hover:bg-paper-200 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Provider Cards */}
        <div className="p-5 space-y-3">
          {providers.map((p) => {
            const isSelected = p.id === selectedProvider;
            const isAvailable = health?.checks?.providers?.[p.id] !== false;

            return (
              <div
                key={p.id}
                onClick={() => setSelectedProvider(p.id)}
                className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all flex items-start gap-3.5 ${
                  isSelected
                    ? 'border-coral-500 bg-coral-50/40 ring-2 ring-coral-500/10'
                    : 'border-paper-300 hover:border-paper-400 bg-white'
                }`}
              >
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    p.id === 'ollama'
                      ? 'bg-amber-100 text-amber-700'
                      : p.id === 'anthropic'
                      ? 'bg-coral-100 text-coral-700'
                      : p.id === 'openai'
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-purple-100 text-purple-700'
                  }`}
                >
                  {p.id === 'ollama' ? (
                    <Cpu className="w-5 h-5" />
                  ) : p.id === 'anthropic' ? (
                    <ShieldCheck className="w-5 h-5" />
                  ) : p.id === 'openai' ? (
                    <Globe className="w-5 h-5" />
                  ) : (
                    <Key className="w-5 h-5" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-ink">
                      {p.name}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        isAvailable
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}
                    >
                      {isAvailable ? 'Ready' : 'Not configured'}
                    </span>
                  </div>

                  <p className="text-[11px] font-mono text-ink-muted truncate mt-0.5">
                    Model: {p.model}
                  </p>

                  <p className="text-[11px] text-ink-faint mt-1">
                    {p.id === 'ollama'
                      ? 'Runs 100% locally with zero cloud API keys.'
                      : p.requires_key
                      ? 'Requires cloud API key configured in .env'
                      : 'Configured gateway endpoint'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3.5 bg-paper-100 border-t border-paper-200 flex justify-end gap-2">
          <button
            onClick={() => setNewChatModalOpen(false)}
            className="px-3 py-1.5 text-xs text-ink-muted hover:text-ink rounded"
          >
            Cancel
          </button>
          <button
            onClick={handleStart}
            className="px-4 py-1.5 bg-coral-500 hover:bg-coral-600 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors"
          >
            Create Session
          </button>
        </div>
      </div>
    </div>
  );
};
