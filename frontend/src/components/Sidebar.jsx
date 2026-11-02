import React from 'react';
import { Database, Plus, Trash2, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export function Sidebar({ repos, activeRepo, onSelectRepo, onOpenAddModal, onDeleteRepo }) {
  return (
    <aside
      style={{
        width: '280px',
        backgroundColor: '#1E293B',
        borderRight: '1px solid #334155',
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 64px)',
        overflowY: 'auto',
      }}
    >
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid #334155',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Repositories
        </span>
        <button
          onClick={onOpenAddModal}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backgroundColor: '#3B82F6',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '6px',
            padding: '6px 10px',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <Plus size={14} /> Add
        </button>
      </div>

      <div style={{ flex: 1, padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {repos.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 12px', color: '#64748B', fontSize: '0.875rem' }}>
            <Database size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
            <p>No repositories indexed yet.</p>
            <p style={{ fontSize: '0.75rem', marginTop: '4px' }}>Click "Add" to index a codebase.</p>
          </div>
        ) : (
          repos.map((repo) => {
            const isActive = activeRepo && activeRepo.repo_id === repo.repo_id;
            return (
              <div
                key={repo.repo_id}
                onClick={() => onSelectRepo(repo.repo_id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  backgroundColor: isActive ? 'rgba(59, 130, 246, 0.15)' : '#0F172A',
                  border: isActive ? '1px solid #3B82F6' : '1px solid #334155',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {repo.status === 'ready' && <CheckCircle2 size={13} color="#10B981" />}
                      {repo.status === 'indexing' && <Clock size={13} color="#F59E0B" />}
                      {repo.status?.startsWith('error') && <AlertCircle size={13} color="#EF4444" />}
                      <span
                        style={{
                          fontSize: '0.875rem',
                          fontWeight: 600,
                          color: '#F1F5F9',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {repo.repo_id}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '4px' }}>
                      {repo.file_count || 0} files · {repo.chunk_count || 0} chunks
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Remove repository ${repo.repo_id}?`)) {
                        onDeleteRepo(repo.repo_id);
                      }
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#64748B',
                      cursor: 'pointer',
                      padding: '4px',
                    }}
                    title="Delete Repository"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}

export default Sidebar;
