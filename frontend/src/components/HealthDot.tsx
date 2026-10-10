import React from 'react';
import { useAppStore } from '../state/store';

export const HealthDot: React.FC = () => {
  const health = useAppStore((s) => s.health);
  const isOk = health?.status === 'ok';

  return (
    <div className="flex items-center gap-2 text-xs text-ink-muted">
      <span
        className={`w-2 h-2 rounded-full ${
          isOk ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]'
        }`}
      />
      <span>{isOk ? 'Stack Ready' : 'Degraded Mode'}</span>
    </div>
  );
};
