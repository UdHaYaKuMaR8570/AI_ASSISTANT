import React from 'react';

interface Props {
  provider: string;
  model: string;
}

export const ProviderBadge: React.FC<Props> = ({ provider, model }) => {
  const isLocal = provider.toLowerCase() === 'ollama';

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-paper-200 border border-paper-300 text-ink-light">
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          isLocal ? 'bg-coral-500' : 'bg-blue-500'
        }`}
      />
      <span className="capitalize font-sans font-medium">{provider}</span>
      <span className="text-ink-faint">/</span>
      <span className="truncate max-w-[120px]">{model}</span>
    </div>
  );
};
