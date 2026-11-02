import React from 'react';
import { NavLink } from 'react-router-dom';
import { Bot, GitBranch, MessageSquare, Bug, BarChart3, Database } from 'lucide-react';

export function Header({ activeRepo }) {
  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        height: '64px',
        backgroundColor: '#1E293B',
        borderBottom: '1px solid #334155',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
        <NavLink
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            textDecoration: 'none',
            color: '#F1F5F9',
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Bot size={22} color="#FFFFFF" />
          </div>
          <span style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
            Repo<span style={{ color: '#3B82F6' }}>Pilot</span>
          </span>
        </NavLink>

        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <NavLink
            to="/chat"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: isActive ? '#3B82F6' : '#94A3B8',
              backgroundColor: isActive ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
            })}
          >
            <MessageSquare size={16} />
            Chat & RAG
          </NavLink>

          <NavLink
            to="/agent"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: isActive ? '#3B82F6' : '#94A3B8',
              backgroundColor: isActive ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
            })}
          >
            <Bug size={16} />
            Bug Investigation
          </NavLink>

          <NavLink
            to="/eval"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: isActive ? '#3B82F6' : '#94A3B8',
              backgroundColor: isActive ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
            })}
          >
            <BarChart3 size={16} />
            Quality Dashboard
          </NavLink>
        </nav>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {activeRepo ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              backgroundColor: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '8px',
              fontSize: '0.8125rem',
              color: '#F1F5F9',
            }}
          >
            <Database size={14} color="#10B981" />
            <span style={{ fontWeight: 600 }}>{activeRepo.repo_id}</span>
            <span style={{ color: '#64748B' }}>({activeRepo.file_count || 0} files)</span>
          </div>
        ) : (
          <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>No Repository Selected</span>
        )}
      </div>
    </header>
  );
}

export default Header;
