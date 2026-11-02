import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import RepoInput from './components/RepoInput';
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';
import AgentPage from './pages/AgentPage';
import EvalPage from './pages/EvalPage';
import useRepo from './hooks/useRepo';
import useChat from './hooks/useChat';
import useEval from './hooks/useEval';

export function App() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const repoState = useRepo();
  const { repos, activeRepo, selectRepo, ingestRepo, deleteRepo } = repoState;

  const chatState = useChat(activeRepo?.repo_id);
  const evalState = useEval();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        backgroundColor: '#0F172A',
        color: '#F1F5F9',
        overflow: 'hidden',
      }}
    >
      <Header activeRepo={activeRepo} />

      <main style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Routes>
          <Route
            path="/"
            element={
              <HomePage
                onOpenAddModal={() => setIsAddModalOpen(true)}
                repoCount={repos.length}
              />
            }
          />

          <Route
            path="/chat"
            element={
              <ChatPage
                repos={repos}
                activeRepo={activeRepo}
                onSelectRepo={selectRepo}
                onOpenAddModal={() => setIsAddModalOpen(true)}
                onDeleteRepo={deleteRepo}
                chatState={chatState}
              />
            }
          />

          <Route
            path="/agent"
            element={
              <AgentPage
                repos={repos}
                activeRepo={activeRepo}
                onSelectRepo={selectRepo}
              />
            }
          />

          <Route
            path="/eval"
            element={
              <EvalPage
                repos={repos}
                activeRepo={activeRepo}
                onSelectRepo={selectRepo}
                evalState={evalState}
              />
            }
          />
        </Routes>
      </main>

      <RepoInput
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onIngest={ingestRepo}
      />
    </div>
  );
}

export default App;
