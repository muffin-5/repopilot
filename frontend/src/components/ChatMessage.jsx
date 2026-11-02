import React from 'react';
import { Bot, User, Clock, Cpu, CheckCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import CitationCard from './CitationCard';

export function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const meta = message.metadata || {};

  return (
    <div
      style={{
        display: 'flex',
        gap: '14px',
        padding: '16px 20px',
        backgroundColor: isUser ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
        borderBottom: '1px solid rgba(51, 65, 85, 0.4)',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          backgroundColor: isUser ? '#3B82F6' : '#1E293B',
          border: isUser ? 'none' : '1px solid #334155',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {isUser ? <User size={18} color="#FFFFFF" /> : <Bot size={18} color="#3B82F6" />}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#F1F5F9' }}>
            {isUser ? 'You' : 'RepoPilot'}
          </span>

          {!isUser && meta.retrievalMode && (
            <span
              style={{
                fontSize: '0.6875rem',
                padding: '2px 8px',
                borderRadius: '12px',
                backgroundColor: 'rgba(59, 130, 246, 0.15)',
                color: '#60A5FA',
                fontWeight: 500,
                textTransform: 'uppercase',
              }}
            >
              {meta.retrievalMode} RAG
            </span>
          )}

          {!isUser && meta.confidence && (
            <span
              style={{
                fontSize: '0.6875rem',
                color: '#10B981',
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
              }}
            >
              <CheckCircle size={12} />
              {Math.round(meta.confidence * 100)}% confidence
            </span>
          )}
        </div>

        {/* Text body */}
        <div
          style={{
            color: '#E2E8F0',
            fontSize: '0.9375rem',
            lineHeight: 1.6,
          }}
          className="markdown-body"
        >
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* Citations section */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <div
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: '#94A3B8',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: '8px',
              }}
            >
              Source Citations ({message.citations.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {message.citations.map((citation, idx) => (
                <CitationCard key={idx} citation={citation} />
              ))}
            </div>
          </div>
        )}

        {/* Latency & tokens footer */}
        {!isUser && (meta.latency || meta.tokensUsed) && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              marginTop: '12px',
              fontSize: '0.75rem',
              color: '#64748B',
            }}
          >
            {meta.latency && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={12} /> {meta.latency}ms
              </span>
            )}
            {meta.tokensUsed && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Cpu size={12} /> {meta.tokensUsed} tokens
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
