import React, { useState } from 'react';
import { Check, X, FileText } from 'lucide-react';

export function EvalTable({ results = [] }) {
  const [filterCategory, setFilterCategory] = useState('all');

  const categories = ['all', ...new Set(results.map((r) => r.category || 'general'))];

  const filtered = filterCategory === 'all'
    ? results
    : results.filter((r) => (r.category || 'general') === filterCategory);

  return (
    <div
      style={{
        backgroundColor: '#1E293B',
        border: '1px solid #334155',
        borderRadius: '10px',
        overflow: 'hidden',
      }}
    >
      {/* Category filter */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 16px',
          borderBottom: '1px solid #334155',
          backgroundColor: '#172033',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: '#94A3B8', fontWeight: 600 }}>Filter:</span>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              backgroundColor: filterCategory === cat ? '#3B82F6' : '#0F172A',
              color: filterCategory === cat ? '#FFFFFF' : '#94A3B8',
              textTransform: 'capitalize',
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155', backgroundColor: '#0F172A', color: '#94A3B8', textAlign: 'left' }}>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Benchmark Question</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Recall@5</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>MRR</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Citation Valid</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Latency</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Tokens</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Cost</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '24px', textAlign: 'center', color: '#64748B' }}>
                  No evaluation queries to display.
                </td>
              </tr>
            ) : (
              filtered.map((item, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid #334155',
                    backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(15, 23, 42, 0.4)',
                  }}
                >
                  <td style={{ padding: '12px 14px', color: '#F1F5F9', maxWidth: '340px' }}>
                    <div style={{ fontWeight: 500 }}>{item.question}</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>
                      {item.answer ? item.answer.slice(0, 80) + '...' : ''}
                    </div>
                  </td>

                  <td style={{ padding: '12px 14px' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: 600,
                        backgroundColor: item.recall_at_5 >= 0.8 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        color: item.recall_at_5 >= 0.8 ? '#10B981' : '#EF4444',
                      }}
                    >
                      {item.recall_at_5}
                    </span>
                  </td>

                  <td style={{ padding: '12px 14px', color: '#E2E8F0', fontWeight: 500 }}>
                    {item.mrr}
                  </td>

                  <td style={{ padding: '12px 14px' }}>
                    {item.citation_valid ? (
                      <Check size={16} color="#10B981" />
                    ) : (
                      <X size={16} color="#EF4444" />
                    )}
                  </td>

                  <td style={{ padding: '12px 14px', color: '#94A3B8' }}>
                    {item.latency_ms ? `${Math.round(item.latency_ms)}ms` : '-'}
                  </td>

                  <td style={{ padding: '12px 14px', color: '#94A3B8' }}>
                    {item.tokens_used || '-'}
                  </td>

                  <td style={{ padding: '12px 14px', color: '#94A3B8' }}>
                    {item.cost ? `$${item.cost.toFixed(4)}` : '$0.000'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default EvalTable;
