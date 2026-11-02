import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, MessageSquare, Bug, BarChart3, ArrowRight, ShieldCheck, Cpu, Code2, Layers } from 'lucide-react';

export function HomePage({ onOpenAddModal, repoCount = 0 }) {
  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '40px 24px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: '56px' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '20px',
            color: '#60A5FA',
            fontSize: '0.8125rem',
            fontWeight: 500,
            marginBottom: '20px',
          }}
        >
          <Bot size={15} /> Production-Grade AI Software Engineering Agent
        </div>

        <h1
          style={{
            fontSize: '2.75rem',
            fontWeight: 800,
            lineHeight: 1.15,
            letterSpacing: '-0.03em',
            color: '#F8FAFC',
            marginBottom: '16px',
          }}
        >
          Understand, Investigate & Fix <br />
          <span style={{ background: 'linear-gradient(135deg, #60A5FA 0%, #3B82F6 50%, #2563EB 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Unfamiliar Codebases
          </span>
        </h1>

        <p style={{ fontSize: '1.125rem', color: '#94A3B8', maxWidth: '680px', margin: '0 auto 28px', lineHeight: 1.6 }}>
          RepoPilot indexes Git repositories using AST-aware syntax chunking and hybrid retrieval (BM25 + Dense Vectors), answers architectural queries with line-level citations, traces bug root causes, and validates performance through quantitative benchmarks.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '14px' }}>
          <Link
            to="/chat"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: '#3B82F6',
              color: '#FFFFFF',
              padding: '12px 24px',
              borderRadius: '8px',
              fontWeight: 600,
              textDecoration: 'none',
              fontSize: '0.9375rem',
            }}
          >
            Launch Chat Workspace <ArrowRight size={16} />
          </Link>
          <button
            onClick={onOpenAddModal}
            style={{
              padding: '12px 20px',
              backgroundColor: '#1E293B',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#F1F5F9',
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: '0.9375rem',
            }}
          >
            + Index New Repository
          </button>
        </div>
      </div>

      {/* 3 Core Modules */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', marginBottom: '48px' }}>
        <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: 'rgba(59, 130, 246, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <MessageSquare size={20} color="#3B82F6" />
          </div>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#F1F5F9', marginBottom: '8px' }}>
            Module A: Repository Intelligence
          </h3>
          <p style={{ fontSize: '0.875rem', color: '#94A3B8', lineHeight: 1.5, marginBottom: '16px' }}>
            Combines Tree-sitter AST syntax chunking with BM25 lexical search and dense semantic embeddings to deliver precise answers backed by exact file paths and line ranges.
          </p>
          <Link to="/chat" style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#3B82F6', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
            Explore Code Q&A <ArrowRight size={14} />
          </Link>
        </div>

        <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <Bug size={20} color="#10B981" />
          </div>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#F1F5F9', marginBottom: '8px' }}>
            Module B: Bug Investigation Agent
          </h3>
          <p style={{ fontSize: '0.875rem', color: '#94A3B8', lineHeight: 1.5, marginBottom: '16px' }}>
            Autonomous ReAct agent with sandboxed tools: parses error reports, traces caller dependencies, discovers regression tests, and drafts candidate code patches.
          </p>
          <Link to="/agent" style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#10B981', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
            Investigate Bugs <ArrowRight size={14} />
          </Link>
        </div>

        <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: 'rgba(168, 85, 247, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <BarChart3 size={20} color="#A855F7" />
          </div>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#F1F5F9', marginBottom: '8px' }}>
            Module C: AI Quality Dashboard
          </h3>
          <p style={{ fontSize: '0.875rem', color: '#94A3B8', lineHeight: 1.5, marginBottom: '16px' }}>
            Rigorous evaluation suite testing Recall@5, MRR, citation validity, abstention on unanswerables, and latency/cost comparisons across retrieval configurations.
          </p>
          <Link to="/eval" style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#A855F7', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
            View Benchmarks <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      {/* Engineering Highlights */}
      <div style={{ backgroundColor: '#0F172A', border: '1px solid #334155', borderRadius: '12px', padding: '28px' }}>
        <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
          Key Technical Contributions
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
          <div style={{ display: 'flex', gap: '12px' }}>
            <Layers size={18} color="#3B82F6" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#F1F5F9' }}>Syntax-Aware Chunking</div>
              <div style={{ fontSize: '0.8125rem', color: '#94A3B8', marginTop: '2px' }}>
                Preserves function & class boundaries rather than arbitrary token slicing.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <Cpu size={18} color="#10B981" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#F1F5F9' }}>Reciprocal Rank Fusion</div>
              <div style={{ fontSize: '0.8125rem', color: '#94A3B8', marginTop: '2px' }}>
                Fuses BM25 sparse lexical tokens with dense vector cosine similarity.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <ShieldCheck size={18} color="#F59E0B" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#F1F5F9' }}>Hallucination & Abstention</div>
              <div style={{ fontSize: '0.8125rem', color: '#94A3B8', marginTop: '2px' }}>
                Explicitly measures whether the agent declines to answer out-of-scope questions.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
