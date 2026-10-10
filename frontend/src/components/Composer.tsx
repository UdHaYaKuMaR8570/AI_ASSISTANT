import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Loader2 } from 'lucide-react';
import { useAppStore } from '../state/store';

export const Composer: React.FC = () => {
  const [text, setText] = useState('');
  const { sendMessage, isStreaming, statusMessage } = useAppStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!text.trim() || isStreaming) return;
    const msg = text.trim();
    setText('');
    sendMessage(msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  useEffect(() => {
    if (!isStreaming && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isStreaming]);

  return (
    <div className="w-full max-w-prose mx-auto">
      <form
        onSubmit={handleSubmit}
        className="relative bg-white rounded-2xl border border-paper-300 shadow-md focus-within:border-coral-500/60 focus-within:ring-2 focus-within:ring-coral-500/10 transition-all overflow-hidden"
      >
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
          rows={2}
          placeholder={isStreaming ? (statusMessage || 'Assistant is generating response...') : 'Ask a product or growth question... (Enter to send, Shift+Enter for newline)'}
          className="w-full px-4 pt-3.5 pb-12 text-sm text-ink placeholder:text-ink-faint focus:outline-hidden resize-none disabled:bg-paper-100 disabled:opacity-60"
        />

        <div className="absolute right-3 bottom-3 flex items-center gap-2">
          <button
            type="submit"
            disabled={!text.trim() || isStreaming}
            className="w-8 h-8 rounded-full bg-coral-500 hover:bg-coral-600 disabled:bg-paper-300 text-white flex items-center justify-center transition-colors shadow-xs disabled:cursor-not-allowed"
          >
            {isStreaming ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
