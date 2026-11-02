import React, { useRef, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import LoadingSpinner from '../components/LoadingSpinner';
import { Database, MessageSquare, Sparkles } from 'lucide-react';

export function ChatPage({
  repos,
  activeRepo,
  onSelectRepo,
  onOpenAddModal,
  onDeleteRepo,
  chatState,
}) {
  const { messages, loading, error, sendMessage, clearMessages } = chatState;
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div style={{ display: 'flex', flex: 1, height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
      {/* Sidebar with repository list */}
      <Sidebar
        repos={repos}
        activeRepo={activeRepo}
        onSelectRepo={onSelectRepo}
        onOpenAddModal={onOpenAddModal}
        onDeleteRepo={onDeleteRepo}
      />

      {/* Main chat workspace */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#0F172A' }}>
        {/* Chat message history container */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {!activeRepo ? (
            <div
              style={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#64748B',
                padding: '24px',
                textAlign: 'center',
              }}
            >
              <Database size={48} style={{ marginBottom: '16px', opacity: 0.6 }} />
              <h2 style={{ fontSize: '1.25rem', color: '#F1F5F9', marginBottom: '8px' }}>
                Select a Repository to Begin
              </h2>
              <p style={{ maxWidth: '440px', fontSize: '0.875rem', marginBottom: '20px' }}>
                Choose an ingested repository from the sidebar or click "Add" to clone and index a new codebase.
              </p>
              <button
                onClick={onOpenAddModal}
                style={{
                  padding: '10px 18px',
                  backgroundColor: '#3B82F6',
                  color: '#FFFFFF',
                  borderRadius: '8px',
                  border: 'none',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                }}
              >
                Index a Repository
              </button>
            </div>
          ) : messages.length === 0 ? (
            <div
              style={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '24px',
                textAlign: 'center',
                color: '#64748B',
              }}
            >
              <MessageSquare size={48} style={{ marginBottom: '16px', color: '#3B82F6', opacity: 0.8 }} />
              <h3 style={{ fontSize: '1.25rem', color: '#F1F5F9', marginBottom: '8px' }}>
                Ask Anything About <span style={{ color: '#3B82F6' }}>{activeRepo.repo_id}</span>
              </h3>
              <p style={{ maxWidth: '520px', fontSize: '0.875rem', marginBottom: '24px' }}>
                RepoPilot retrieves AST-parsed code snippets, checks citations, and responds with exact file and line references.
              </p>

              {/* Starter questions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: '480px', width: '100%' }}>
                {[
                  'How does authentication and authorization work in this project?',
                  'Where is the main request routing and middleware configured?',
                  'Which files would I need to touch to add a new database model?',
                  'Find the test suites and describe the testing strategy used.',
                ].map((promptText, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(promptText, 'hybrid')}
                    style={{
                      padding: '10px 14px',
                      backgroundColor: '#1E293B',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#E2E8F0',
                      fontSize: '0.8125rem',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'border-color 0.15s ease',
                    }}
                  >
                    "{promptText}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div>
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}

              {loading && (
                <div style={{ padding: '24px 20px', display: 'flex', alignItems: 'center', gap: '12px', color: '#94A3B8' }}>
                  <LoadingSpinner size="small" />
                  <span style={{ fontSize: '0.875rem' }}>
                    Retrieving AST code snippets & reasoning over codebase...
                  </span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Chat input box */}
        <ChatInput
          onSendMessage={sendMessage}
          disabled={!activeRepo}
          loading={loading}
        />
      </div>
    </div>
  );
}

export default ChatPage;
