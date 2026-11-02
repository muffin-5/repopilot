import React, { useState } from 'react';
import { Copy, Check, FileCode } from 'lucide-react';

export function CodeBlock({ code, language = 'python', filePath = '', startLine = 1 }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = code.trim().split('\n');

  return (
    <div
      style={{
        borderRadius: '8px',
        overflow: 'hidden',
        backgroundColor: '#0F172A',
        border: '1px solid #334155',
        margin: '12px 0',
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        fontSize: '0.8125rem',
      }}
    >
      {filePath && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 14px',
            backgroundColor: '#1E293B',
            borderBottom: '1px solid #334155',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94A3B8' }}>
            <FileCode size={15} color="#3B82F6" />
            <span style={{ fontWeight: 500, color: '#F1F5F9' }}>{filePath}</span>
          </div>
          <button
            onClick={handleCopy}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: 'none',
              border: 'none',
              color: copied ? '#10B981' : '#64748B',
              cursor: 'pointer',
              fontSize: '0.75rem',
            }}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      )}

      <div style={{ padding: '12px 0', overflowX: 'auto', display: 'flex' }}>
        {/* Line Numbers */}
        <div
          style={{
            userSelect: 'none',
            textAlign: 'right',
            padding: '0 12px',
            color: '#475569',
            borderRight: '1px solid #1E293B',
          }}
        >
          {lines.map((_, idx) => (
            <div key={idx} style={{ lineHeight: '1.5' }}>
              {startLine + idx}
            </div>
          ))}
        </div>

        {/* Code Content */}
        <div style={{ padding: '0 16px', flex: 1, color: '#E2E8F0' }}>
          {lines.map((line, idx) => (
            <div key={idx} style={{ lineHeight: '1.5', whiteSpace: 'pre' }}>
              {line || ' '}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default CodeBlock;
