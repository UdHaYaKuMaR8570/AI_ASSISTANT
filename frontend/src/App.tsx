import React, { useEffect } from 'react';
import { FileCode, Menu, Plus } from 'lucide-react';
import { useAppStore } from './state/store';
import { Sidebar } from './components/Sidebar';
import { Chat } from './components/Chat';
import { Composer } from './components/Composer';
import { QuickActions } from './components/QuickActions';
import { ProviderBadge } from './components/ProviderBadge';
import { NewChatModal } from './components/NewChatModal';
import { ArtifactPanel } from './artifacts/ArtifactPanel';

export const App: React.FC = () => {
  const {
    init,
    sessions,
    activeSessionId,
    setNewChatModalOpen,
    isArtifactPanelOpen,
    setArtifactPanelOpen,
    artifacts,
  } = useAppStore();

  useEffect(() => {
    init();
  }, [init]);

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const hasArtifacts = artifacts.length > 0;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-paper-100 font-sans text-ink">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Center Chat View */}
      <main className="flex-1 flex flex-col h-full min-w-0 bg-paper-100 relative">
        {/* Top Chat Header */}
        <header className="h-14 border-b border-paper-300 px-6 flex items-center justify-between bg-paper-100/80 backdrop-blur-xs z-10">
          <div className="flex items-center gap-3 truncate mr-2">
            <h2 className="font-serif font-bold text-sm text-ink truncate">
              {activeSession ? activeSession.title : 'Lenny Growth Assistant'}
            </h2>
            {activeSession && (
              <ProviderBadge
                provider={activeSession.provider}
                model={activeSession.model}
              />
            )}
          </div>

          <div className="flex items-center gap-2">
            {hasArtifacts && (
              <button
                onClick={() => setArtifactPanelOpen(!isArtifactPanelOpen)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                  isArtifactPanelOpen
                    ? 'bg-ink text-paper-50 border-ink'
                    : 'bg-white border-paper-300 text-ink hover:bg-paper-200'
                }`}
              >
                <FileCode className="w-3.5 h-3.5 text-coral-500" />
                <span>Artifacts ({artifacts.length})</span>
              </button>
            )}

            <button
              onClick={() => setNewChatModalOpen(true)}
              className="sm:hidden p-1.5 bg-coral-500 text-white rounded-md"
              title="New Chat"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Chat Message Stream */}
        <Chat />

        {/* Bottom Composer and Quick Actions */}
        <div className="p-4 bg-gradient-to-t from-paper-100 via-paper-100 to-transparent flex flex-col gap-2.5 z-10">
          <div className="w-full max-w-prose mx-auto">
            <QuickActions />
          </div>
          <Composer />
        </div>
      </main>

      {/* Right Slide-in Artifact Panel */}
      <ArtifactPanel />

      {/* New Conversation Modal */}
      <NewChatModal />
    </div>
  );
};

export default App;
