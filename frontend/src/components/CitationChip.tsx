import React from 'react';
import { ExternalLink, Play } from 'lucide-react';
import { Citation } from '../api/types';

interface Props {
  citation: Citation;
}

function formatTs(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export const CitationChip: React.FC<Props> = ({ citation }) => {
  return (
    <a
      href={citation.youtube_url || '#'}
      target="_blank"
      rel="noopener noreferrer"
      className="group inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs bg-paper-100 hover:bg-paper-200 border border-paper-300 hover:border-coral-500/50 transition-all text-ink shadow-xs"
    >
      <div className="w-5 h-5 rounded-full bg-coral-50 flex items-center justify-center text-coral-600 group-hover:bg-coral-500 group-hover:text-white transition-colors">
        <Play className="w-2.5 h-2.5 fill-current ml-0.5" />
      </div>

      <div className="flex flex-col text-left">
        <span className="font-semibold text-ink group-hover:text-coral-600 transition-colors truncate max-w-[160px]">
          {citation.guest}
        </span>
        <span className="text-[10px] text-ink-muted truncate max-w-[160px]">
          {citation.title} • {formatTs(citation.start_ts)}
        </span>
      </div>

      <ExternalLink className="w-3 h-3 text-ink-faint opacity-0 group-hover:opacity-100 transition-opacity ml-1" />
    </a>
  );
};
