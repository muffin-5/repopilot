import React, { useState } from 'react';
import { FileCode, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import CodeBlock from './CodeBlock';

export function CitationCard({ citation, onOpenFull }) {
  const [expanded, setExpanded] = useState(false);
  const scorePercent = Math.min(100, Math.round((citation.relevance_score || 0.1) * 100));

  return (
    <div
      style={{
        borderRadius: '8px',
        backgroundColor: '#1E293B',
        border: '1px solid #334155',
        overflow: 'hidden',
        transition: 'border-color 0.15s ease',
      }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 14px',
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileCode size={16} color="#3B82F6" />
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#F1F5F9' }}>
            {citation.file_path}
          </span>
          <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
            Lines {citation.start_line}-{citation.end_line}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Relevance Bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.6875rem', color: '#64748B' }}>Match</span>
            <div
              style={{
                width: '48px',
                height: '4px',
                backgroundColor: '#0F172A',
                borderRadius: '2px',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${scorePercent}%`,
                  height: '100%',
                  backgroundColor: scorePercent > 70 ? '#10B981' : '#3B82F6',
                }}
              />
            </div>
          </div>

          {expanded ? <ChevronUp size={16} color="#94A3B8" /> : <ChevronDown size={16} color="#94A3B8" />}
        </div>
      </div>

      {expanded && (
        <div style={{ padding: '0 14px 14px', borderTop: '1px solid #334155', backgroundColor: '#131D2F' }}>
          <CodeBlock
            code={citation.content}
            filePath=""
            startLine={citation.start_line}
          />
        </div>
      )}
    </div>
  );
}

export default CitationCard;
