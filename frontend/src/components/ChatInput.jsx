import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';

export function ChatInput({ onSendMessage, disabled, loading }) {
  const [question, setQuestion] = useState('');
  const [retrievalMode, setRetrievalMode] = useState('hybrid');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [question]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!question.trim() || disabled || loading) return;

    onSendMessage(question.trim(), retrievalMode);
    setQuestion('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      style={{
        padding: '16px 20px',
        backgroundColor: '#1E293B',
        borderTop: '1px solid #334155',
      }}
    >
      <form onSubmit={handleSubmit}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.75rem', color: '#94A3B8', fontWeight: 500 }}>
              Retrieval Strategy:
            </span>
            <select
              value={retrievalMode}
              onChange={(e) => setRetrievalMode(e.target.value)}
              disabled={disabled || loading}
              style={{
                backgroundColor: '#0F172A',
                border: '1px solid #334155',
                borderRadius: '6px',
                color: '#F1F5F9',
                fontSize: '0.75rem',
                padding: '4px 8px',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="hybrid">Proposed: Hybrid (AST + BM25 + Vector)</option>
              <option value="vector">Baseline B: Vector Only (AST-aware)</option>
              <option value="bm25">Lexical: BM25 Only</option>
            </select>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
            Press Enter to send, Shift+Enter for new line
          </span>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: '10px',
            backgroundColor: '#0F172A',
            border: '1px solid #334155',
            borderRadius: '10px',
            padding: '8px 12px',
          }}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || loading}
            placeholder={
              disabled
                ? 'Select or index a repository first...'
                : 'Ask how authentication works, trace an API route, or locate functions...'
            }
            style={{
              flex: 1,
              backgroundColor: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#F1F5F9',
              fontSize: '0.875rem',
              resize: 'none',
              maxHeight: '160px',
              fontFamily: 'inherit',
            }}
          />

          <button
            type="submit"
            disabled={!question.trim() || disabled || loading}
            style={{
              backgroundColor: !question.trim() || disabled || loading ? '#334155' : '#3B82F6',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              padding: '8px 12px',
              cursor: !question.trim() || disabled || loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background-color 0.15s ease',
            }}
          >
            <Send size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}

export default ChatInput;
