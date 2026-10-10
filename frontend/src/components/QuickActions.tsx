import React from 'react';
import { BookOpen, FileText, Sparkles, TrendingUp } from 'lucide-react';
import { useAppStore } from '../state/store';

export const QuickActions: React.FC = () => {
  const { sendMessage, isStreaming, messages } = useAppStore();

  const handleAction = (promptText: string) => {
    if (isStreaming) return;
    sendMessage(promptText);
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar text-xs">
      {hasMessages ? (
        <>
          <button
            disabled={isStreaming}
            onClick={() => handleAction('Turn your last response into a publishable Ship 30 atomic essay.')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-paper-100 hover:bg-paper-200 border border-paper-300 text-ink-light transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            <BookOpen className="w-3.5 h-3.5 text-coral-500" />
            <span>✍️ Ship 30 essay</span>
          </button>
          <button
            disabled={isStreaming}
            onClick={() => handleAction('Create an interactive HTML artifact summarizing these key findings with an actionable checklist.')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-paper-100 hover:bg-paper-200 border border-paper-300 text-ink-light transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            <FileText className="w-3.5 h-3.5 text-coral-500" />
            <span>📄 Turn into artifact</span>
          </button>
        </>
      ) : (
        <>
          <button
            disabled={isStreaming}
            onClick={() => handleAction('What are the best frameworks for finding product-market fit according to Lenny’s guests?')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-paper-100 hover:bg-paper-200 border border-paper-300 text-ink-light transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            <Sparkles className="w-3.5 h-3.5 text-coral-500" />
            <span>PMF Frameworks</span>
          </button>
          <button
            disabled={isStreaming}
            onClick={() => handleAction('How do top product teams run pricing and packaging experiments?')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-paper-100 hover:bg-paper-200 border border-paper-300 text-ink-light transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            <TrendingUp className="w-3.5 h-3.5 text-coral-500" />
            <span>Pricing Experiments</span>
          </button>
          <button
            disabled={isStreaming}
            onClick={() => handleAction('Write a Ship 30 essay on why retention is more important than acquisition.')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-paper-100 hover:bg-paper-200 border border-paper-300 text-ink-light transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            <BookOpen className="w-3.5 h-3.5 text-coral-500" />
            <span>Retention vs Acquisition Essay</span>
          </button>
        </>
      )}
    </div>
  );
};
