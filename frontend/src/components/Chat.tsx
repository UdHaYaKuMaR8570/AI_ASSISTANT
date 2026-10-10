import React, { useEffect, useRef } from 'react';
import { Compass, FileText, Sparkles } from 'lucide-react';
import { useAppStore } from '../state/store';
import { CitationChip } from './CitationChip';
import { StatusLine } from './StatusLine';
import { MarkdownView } from '../artifacts/MarkdownView';

export const Chat: React.FC = () => {
  const { messages, isStreaming, statusMessage, sendMessage } = useAppStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, statusMessage]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-prose mx-auto">
        <div className="w-12 h-12 rounded-2xl bg-coral-50 flex items-center justify-center text-coral-600 mb-4 shadow-sm border border-coral-200">
          <Sparkles className="w-6 h-6" />
        </div>
        <h2 className="font-serif text-2xl font-bold text-ink mb-2">
          The Lenny Growth Assistant
        </h2>
        <p className="text-sm text-ink-muted leading-relaxed mb-8">
          Answers grounded strictly in 300+ episodes of Lenny’s Podcast. Every claim is cited directly to original guest audio and YouTube timestamps.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
          {[
            {
              title: "Product-Market Fit",
              prompt: "How did Superhuman and Airbnb know they reached product-market fit according to Lenny's guests?",
              icon: Compass,
            },
            {
              title: "Pricing & Packaging",
              prompt: "What are Patrick Campbell's core rules for pricing SaaS products without losing customers?",
              icon: FileText,
            },
            {
              title: "Ship 30 Essay: Retention",
              prompt: "Write a Ship 30 atomic essay on why retention curves matter more than virality.",
              icon: Sparkles,
            },
            {
              title: "Career Growth for PMs",
              prompt: "What advice did Shreyas Doshi share on high-agency vs victim mindsets in product leadership?",
              icon: Compass,
            },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                onClick={() => sendMessage(item.prompt)}
                className="p-3.5 rounded-xl border border-paper-300 hover:border-coral-500/50 bg-white hover:bg-paper-100/50 text-left transition-all shadow-xs group"
              >
                <div className="flex items-center gap-2 mb-1 text-ink font-semibold text-xs group-hover:text-coral-600">
                  <Icon className="w-3.5 h-3.5 text-coral-500" />
                  <span>{item.title}</span>
                </div>
                <p className="text-xs text-ink-muted line-clamp-2 leading-relaxed">
                  {item.prompt}
                </p>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 max-w-prose mx-auto w-full">
      {messages.map((m) => {
        const isUser = m.role === 'user';
        const isRefusal = m.content.includes("don't appear to cover this topic");

        return (
          <div
            key={m.id}
            className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} animate-in fade-in duration-200`}
          >
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                isUser
                  ? 'bg-ink text-paper-50 rounded-br-xs shadow-sm font-sans'
                  : isRefusal
                  ? 'bg-paper-200 border border-paper-300 text-ink-muted italic rounded-bl-xs'
                  : 'bg-white border border-paper-300 text-ink shadow-xs rounded-bl-xs'
              }`}
            >
              {isUser ? (
                <p className="whitespace-pre-wrap">{m.content}</p>
              ) : (
                <MarkdownView content={m.content} />
              )}
            </div>

            {/* Citation Chips */}
            {!isUser && m.citations && m.citations.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-2 max-w-full">
                {m.citations.map((c) => (
                  <CitationChip key={c.chunk_id} citation={c} />
                ))}
              </div>
            )}
          </div>
        );
      })}

      {/* Streaming / Tool status indicator */}
      {isStreaming && statusMessage && (
        <div className="flex justify-start">
          <StatusLine message={statusMessage} />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
