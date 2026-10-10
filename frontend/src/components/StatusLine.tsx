import React from 'react';
import { Loader2 } from 'lucide-react';

interface Props {
  message: string;
}

export const StatusLine: React.FC<Props> = ({ message }) => {
  return (
    <div className="flex items-center gap-2.5 py-2 px-3 rounded-md bg-paper-200/60 border border-paper-300 text-xs text-ink-muted animate-pulse">
      <Loader2 className="w-3.5 h-3.5 animate-spin text-coral-500" />
      <span className="font-mono text-ink-light">{message}</span>
    </div>
  );
};
