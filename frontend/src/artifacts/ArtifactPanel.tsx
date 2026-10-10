import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Code, Download, Eye, X } from 'lucide-react';
import { useAppStore } from '../state/store';
import { HtmlSandbox } from './HtmlSandbox';
import { MarkdownView } from './MarkdownView';

export const ArtifactPanel: React.FC = () => {
  const {
    artifacts,
    activeArtifactGroupId,
    isArtifactPanelOpen,
    setArtifactPanelOpen,
    setActiveArtifactGroupId,
  } = useAppStore();

  const [mode, setMode] = useState<'preview' | 'source'>('preview');
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);

  if (!isArtifactPanelOpen) return null;

  // Group artifacts by group_id
  const groupMap = new Map<string, typeof artifacts>();
  for (const a of artifacts) {
    const list = groupMap.get(a.group_id) || [];
    list.push(a);
    groupMap.set(a.group_id, list);
  }

  const groupIds = Array.from(groupMap.keys());
  const currentGroupId = activeArtifactGroupId || groupIds[0];
  const groupVersions = currentGroupId ? groupMap.get(currentGroupId) || [] : [];
  
  // Sort versions descending to get latest
  const sortedVersions = [...groupVersions].sort((a, b) => b.version - a.version);
  const activeArtifact =
    selectedVersion !== null
      ? groupVersions.find((a) => a.version === selectedVersion) || sortedVersions[0]
      : sortedVersions[0];

  const handleDownload = () => {
    if (!activeArtifact) return;
    const ext = activeArtifact.kind === 'html' ? 'html' : 'md';
    const blob = new Blob([activeArtifact.content], {
      type: activeArtifact.kind === 'html' ? 'text/html' : 'text/markdown',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${activeArtifact.title.replace(/\s+/g, '_').toLowerCase()}_v${activeArtifact.version}.${ext}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <aside className="w-full lg:w-[480px] xl:w-[540px] flex-shrink-0 h-full bg-paper-50 border-l border-paper-300 flex flex-col z-20 shadow-xl transition-all">
      {/* Top Header */}
      <div className="p-4 border-b border-paper-300 flex items-center justify-between bg-paper-100">
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          {groupIds.map((gid) => {
            const arts = groupMap.get(gid) || [];
            const latest = arts[0];
            const isActive = gid === currentGroupId;
            return (
              <button
                key={gid}
                onClick={() => {
                  setActiveArtifactGroupId(gid);
                  setSelectedVersion(null);
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-ink text-paper-50 shadow-sm'
                    : 'bg-paper-200 text-ink-muted hover:bg-paper-300'
                }`}
              >
                {latest?.title || 'Artifact'}
              </button>
            );
          })}
        </div>
        <button
          onClick={() => setArtifactPanelOpen(false)}
          className="p-1 text-ink-muted hover:text-ink hover:bg-paper-200 rounded transition-colors"
          title="Close Artifact Panel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {activeArtifact ? (
        <>
          {/* Controls Bar: Title, Version Stepper, Mode, Download */}
          <div className="px-4 py-3 border-b border-paper-200 flex items-center justify-between bg-paper-50 gap-2">
            <div>
              <h3 className="font-serif font-bold text-sm text-ink truncate max-w-[200px]">
                {activeArtifact.title}
              </h3>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 bg-paper-200 text-ink-muted rounded">
                  {activeArtifact.kind}
                </span>
                {activeArtifact.change_note && (
                  <span className="text-xs text-ink-faint italic truncate max-w-[150px]">
                    {activeArtifact.change_note}
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Version Stepper */}
              {groupVersions.length > 1 && (
                <div className="flex items-center gap-1 bg-paper-200 px-2 py-1 rounded text-xs">
                  <button
                    disabled={activeArtifact.version <= 1}
                    onClick={() => setSelectedVersion(activeArtifact.version - 1)}
                    className="disabled:opacity-30 hover:text-coral-500"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                  </button>
                  <span className="font-mono font-medium px-1">v{activeArtifact.version}</span>
                  <button
                    disabled={activeArtifact.version >= sortedVersions[0].version}
                    onClick={() => setSelectedVersion(activeArtifact.version + 1)}
                    className="disabled:opacity-30 hover:text-coral-500"
                  >
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {/* Preview / Source Mode */}
              <div className="flex bg-paper-200 p-0.5 rounded text-xs">
                <button
                  onClick={() => setMode('preview')}
                  className={`p-1.5 rounded ${mode === 'preview' ? 'bg-white shadow-xs text-ink' : 'text-ink-muted'}`}
                  title="Rendered Preview"
                >
                  <Eye className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setMode('source')}
                  className={`p-1.5 rounded ${mode === 'source' ? 'bg-white shadow-xs text-ink' : 'text-ink-muted'}`}
                  title="Source Code"
                >
                  <Code className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Download */}
              <button
                onClick={handleDownload}
                className="p-1.5 text-ink-muted hover:text-ink hover:bg-paper-200 rounded transition-colors"
                title="Download Artifact"
              >
                <Download className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Main Viewer */}
          <div className="flex-1 overflow-y-auto p-5">
            {mode === 'preview' ? (
              activeArtifact.kind === 'html' ? (
                <HtmlSandbox content={activeArtifact.content} />
              ) : (
                <MarkdownView content={activeArtifact.content} />
              )
            ) : (
              <pre className="bg-[#1A1611] text-[#FAF6F0] p-4 rounded-lg font-mono text-xs overflow-x-auto leading-relaxed">
                {activeArtifact.content}
              </pre>
            )}
          </div>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center text-ink-muted text-sm">
          No artifact selected
        </div>
      )}
    </aside>
  );
};
