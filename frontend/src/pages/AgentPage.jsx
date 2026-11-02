import React, { useState } from 'react';
import { Bug, Play, CheckCircle2, FileCode, TestTube, GitCommit, AlertTriangle } from 'lucide-react';
import { investigateBug } from '../services/api';
import CodeBlock from '../components/CodeBlock';
import LoadingSpinner from '../components/LoadingSpinner';

export function AgentPage({ repos, activeRepo, onSelectRepo }) {
  const [bugDescription, setBugDescription] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [stackTrace, setStackTrace] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleInvestigate = async (e) => {
    e.preventDefault();
    if (!activeRepo || !bugDescription.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const data = await investigateBug(
        activeRepo.repo_id,
        bugDescription.trim(),
        errorMessage.trim(),
        stackTrace.trim()
      );
      setAnalysisResult(data);
    } catch (err) {
      setError(err.message || 'Bug investigation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '28px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      {/* Title */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Bug size={18} color="#10B981" />
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#F1F5F9' }}>
            Bug Investigation Agent
          </h2>
        </div>
        <p style={{ color: '#94A3B8', fontSize: '0.875rem' }}>
          Autonomous tool-using workflow: analyzes bug symptoms, searches AST code chunks, traces imports, finds relevant tests, and synthesizes candidate patches.
        </p>
      </div>

      {/* Target Repo Picker */}
      <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '0.875rem', fontWeight: 500, color: '#94A3B8' }}>Target Repository:</span>
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
          {repos.length === 0 && <option value="">No repositories available</option>}
          {repos.map((r) => (
            <option key={r.repo_id} value={r.repo_id}>
              {r.repo_id} ({r.file_count || 0} files)
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: analysisResult ? '1fr 1fr' : '1fr', gap: '24px' }}>
        {/* Input Form */}
        <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '12px', padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#F1F5F9', marginBottom: '16px' }}>
            Submit Bug Report
          </h3>

          {error && (
            <div style={{ padding: '12px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#EF4444', fontSize: '0.875rem', marginBottom: '16px' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleInvestigate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#94A3B8', marginBottom: '6px' }}>
                Bug Description / Symptoms *
              </label>
              <textarea
                required
                rows={3}
                placeholder="e.g. When authenticating with expired refresh tokens, the API crashes with 500 instead of returning 401 Unauthorized."
                value={bugDescription}
                onChange={(e) => setBugDescription(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  backgroundColor: '#0F172A',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#F1F5F9',
                  fontSize: '0.875rem',
                  outline: 'none',
                  fontFamily: 'inherit',
                  resize: 'vertical',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#94A3B8', marginBottom: '6px' }}>
                Error Message (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. jwt.exceptions.ExpiredSignatureError: Signature has expired"
                value={errorMessage}
                onChange={(e) => setErrorMessage(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  backgroundColor: '#0F172A',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#F1F5F9',
                  fontSize: '0.875rem',
                  outline: 'none',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, color: '#94A3B8', marginBottom: '6px' }}>
                Stack Trace (Optional)
              </label>
              <textarea
                rows={4}
                placeholder="File 'app/services/auth.py', line 45, in verify_token\n  payload = jwt.decode(token)..."
                value={stackTrace}
                onChange={(e) => setStackTrace(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  backgroundColor: '#0F172A',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#F1F5F9',
                  fontSize: '0.8125rem',
                  outline: 'none',
                  fontFamily: "'JetBrains Mono', monospace",
                  resize: 'vertical',
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading || !activeRepo || !bugDescription.trim()}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '12px 20px',
                backgroundColor: '#10B981',
                border: 'none',
                borderRadius: '8px',
                color: '#FFFFFF',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: loading || !activeRepo || !bugDescription.trim() ? 'not-allowed' : 'pointer',
                opacity: loading || !activeRepo || !bugDescription.trim() ? 0.6 : 1,
              }}
            >
              {loading ? (
                <LoadingSpinner size="small" text="Executing ReAct investigation loop..." />
              ) : (
                <>
                  <Play size={16} /> Run Bug Investigation
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        {analysisResult && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Root Cause Analysis */}
            <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#F1F5F9' }}>
                  Root Cause Investigation
                </h4>
                <span style={{ fontSize: '0.75rem', color: '#10B981', fontWeight: 600 }}>
                  {Math.round(analysisResult.confidence * 100)}% Confidence
                </span>
              </div>
              <div style={{ fontSize: '0.875rem', color: '#CBD5E1', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                {analysisResult.analysis}
              </div>
            </div>

            {/* Relevant Files */}
            <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
              <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '12px' }}>
                Identified Culprit Files ({analysisResult.relevant_files?.length || 0})
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {analysisResult.relevant_files?.map((f, idx) => (
                  <span
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 10px',
                      backgroundColor: '#0F172A',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      fontSize: '0.8125rem',
                      color: '#60A5FA',
                    }}
                  >
                    <FileCode size={14} /> {f}
                  </span>
                ))}
              </div>
            </div>

            {/* Candidate Patches */}
            {analysisResult.suggested_patches && analysisResult.suggested_patches.length > 0 && (
              <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '12px' }}>
                  Candidate Patch Suggestion
                </h4>
                {analysisResult.suggested_patches.map((p, idx) => (
                  <div key={idx}>
                    <div style={{ fontSize: '0.8125rem', color: '#94A3B8', marginBottom: '8px' }}>
                      {p.explanation}
                    </div>
                    <CodeBlock
                      code={p.suggested_code}
                      filePath={p.file_path}
                      language="python"
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Related Tests */}
            {analysisResult.related_tests && analysisResult.related_tests.length > 0 && (
              <div style={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', marginBottom: '12px' }}>
                  Target Regression Test Files
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {analysisResult.related_tests.map((t, idx) => (
                    <span
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '4px 10px',
                        backgroundColor: '#0F172A',
                        border: '1px solid #334155',
                        borderRadius: '6px',
                        fontSize: '0.8125rem',
                        color: '#34D399',
                      }}
                    >
                      <TestTube size={14} /> {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentPage;
