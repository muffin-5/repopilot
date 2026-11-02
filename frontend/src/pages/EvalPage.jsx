import React, { useState } from 'react';
import { BarChart3, Play, GitCompare, CheckCircle2, TrendingUp, DollarSign, Clock } from 'lucide-react';
import MetricsCard from '../components/MetricsCard';
import EvalTable from '../components/EvalTable';
import LoadingSpinner from '../components/LoadingSpinner';

export function EvalPage({ repos, activeRepo, onSelectRepo, evalState }) {
  const { results, summary, comparisons, loading, error, runEvaluation, compareConfigurations } = evalState;
  const [selectedModes, setSelectedModes] = useState(['hybrid', 'vector', 'bm25']);
  const [activeTab, setActiveTab] = useState('overview');

  const handleRunBenchmark = async () => {
    if (!activeRepo) return;
    await runEvaluation(activeRepo.repo_id, null, selectedModes);
  };

  const handleRunComparison = async () => {
    if (!activeRepo) return;
    await compareConfigurations(activeRepo.repo_id, selectedModes);
  };

  // Get active summary (hybrid preferred)
  const activeSummary = summary?.['hybrid'] || summary?.[selectedModes[0]] || null;
  const activeResults = results?.['hybrid'] || results?.[selectedModes[0]] || [];

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '28px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'rgba(168, 85, 247, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BarChart3 size={18} color="#A855F7" />
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#F1F5F9' }}>
              AI Quality & Retrieval Dashboard
            </h2>
          </div>
          <p style={{ color: '#94A3B8', fontSize: '0.875rem' }}>
            Ablation benchmarks evaluating Recall@5, Mean Reciprocal Rank (MRR), Citation Groundedness, and Inference Latency.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            value={activeRepo ? activeRepo.repo_id : ''}
            onChange={(e) => onSelectRepo(e.target.value)}
            style={{
              padding: '8px 12px',
              backgroundColor: '#1E293B',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#F1F5F9',
              fontSize: '0.875rem',
              outline: 'none',
            }}
          >
            {repos.length === 0 && <option value="">No repos available</option>}
            {repos.map((r) => (
              <option key={r.repo_id} value={r.repo_id}>
                {r.repo_id}
              </option>
            ))}
          </select>

          <button
            onClick={handleRunBenchmark}
            disabled={loading || !activeRepo}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              backgroundColor: '#3B82F6',
              border: 'none',
              borderRadius: '8px',
              color: '#FFFFFF',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: loading || !activeRepo ? 'not-allowed' : 'pointer',
              opacity: loading || !activeRepo ? 0.6 : 1,
            }}
          >
            <Play size={15} /> Run Benchmark
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#EF4444', fontSize: '0.875rem', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {loading && (
        <div style={{ padding: '40px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
          <LoadingSpinner size="large" />
          <span style={{ color: '#94A3B8', fontSize: '0.875rem' }}>
            Running systematic evaluation across retrieval baselines...
          </span>
        </div>
      )}

      {/* Metrics Row */}
      {activeSummary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '28px' }}>
          <MetricsCard
            title="Recall@5"
            value={(activeSummary.avg_recall_at_5 * 100).toFixed(1)}
            unit="%"
            trend={activeSummary.avg_recall_at_5 > 0.7 ? 'up' : 'neutral'}
            description="Relevance in top-5 chunks"
          />
          <MetricsCard
            title="MRR"
            value={activeSummary.avg_mrr.toFixed(3)}
            trend={activeSummary.avg_mrr > 0.5 ? 'up' : 'neutral'}
            description="Mean Reciprocal Rank"
          />
          <MetricsCard
            title="Citation Accuracy"
            value={(activeSummary.citation_accuracy * 100).toFixed(1)}
            unit="%"
            trend="up"
            description="Verified source citations"
          />
          <MetricsCard
            title="Average Latency"
            value={Math.round(activeSummary.avg_latency_ms)}
            unit="ms"
            description="End-to-end query time"
          />
        </div>
      )}

      {/* Comparative Ablation Study Table */}
      {summary && Object.keys(summary).length > 1 && (
        <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '12px', padding: '20px', marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <GitCompare size={18} color="#3B82F6" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#F1F5F9' }}>
              Retrieval Strategy Comparison (Ablation Study)
            </h3>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left', color: '#94A3B8' }}>
                <th style={{ padding: '8px 12px' }}>Configuration</th>
                <th style={{ padding: '8px 12px' }}>Recall@5</th>
                <th style={{ padding: '8px 12px' }}>MRR</th>
                <th style={{ padding: '8px 12px' }}>Citation Validity</th>
                <th style={{ padding: '8px 12px' }}>Latency</th>
                <th style={{ padding: '8px 12px' }}>Est. Cost</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(summary).map(([mode, s]) => (
                <tr key={mode} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.4)' }}>
                  <td style={{ padding: '12px', fontWeight: 600, color: mode === 'hybrid' ? '#60A5FA' : '#F1F5F9' }}>
                    {mode === 'hybrid'
                      ? 'Proposed: Hybrid (AST + BM25 + Vector)'
                      : mode === 'vector'
                      ? 'Baseline B: Vector Only (AST-aware)'
                      : 'Baseline: Lexical BM25 Only'}
                  </td>
                  <td style={{ padding: '12px', color: '#10B981', fontWeight: 600 }}>
                    {(s.avg_recall_at_5 * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px', color: '#E2E8F0' }}>{s.avg_mrr.toFixed(3)}</td>
                  <td style={{ padding: '12px', color: '#E2E8F0' }}>
                    {(s.citation_accuracy * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px', color: '#94A3B8' }}>{Math.round(s.avg_latency_ms)}ms</td>
                  <td style={{ padding: '12px', color: '#94A3B8' }}>${s.total_cost.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detailed Benchmark Questions Table */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#F1F5F9' }}>
            Detailed Benchmark Queries ({activeResults.length})
          </h3>
        </div>
        <EvalTable results={activeResults} />
      </div>
    </div>
  );
}

export default EvalPage;
