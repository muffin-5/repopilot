import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

export function MetricsCard({ title, value, unit = '', description = '', trend = null, comparison = '' }) {
  return (
    <div
      style={{
        backgroundColor: '#1E293B',
        border: '1px solid #334155',
        borderRadius: '10px',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {title}
        </span>
        {trend && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: trend === 'up' ? '#10B981' : trend === 'down' ? '#EF4444' : '#64748B',
            }}
          >
            {trend === 'up' && <ArrowUpRight size={14} />}
            {trend === 'down' && <ArrowDownRight size={14} />}
            {trend === 'neutral' && <Minus size={14} />}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', margin: '4px 0 8px' }}>
        <span style={{ fontSize: '1.75rem', fontWeight: 700, color: '#F1F5F9' }}>{value}</span>
        {unit && <span style={{ fontSize: '0.875rem', color: '#94A3B8' }}>{unit}</span>}
      </div>

      {(description || comparison) && (
        <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
          {comparison ? (
            <span style={{ color: '#10B981', fontWeight: 500 }}>{comparison}</span>
          ) : (
            description
          )}
        </div>
      )}
    </div>
  );
}

export default MetricsCard;
