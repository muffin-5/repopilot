import React from 'react';

export function LoadingSpinner({ size = 'medium', text = '' }) {
  const sizeClasses = {
    small: 'w-4 h-4 border-2',
    medium: 'w-8 h-8 border-3',
    large: 'w-12 h-12 border-4',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
      <div
        style={{
          width: size === 'small' ? '16px' : size === 'large' ? '48px' : '28px',
          height: size === 'small' ? '16px' : size === 'large' ? '48px' : '28px',
          border: '3px solid rgba(59, 130, 246, 0.2)',
          borderTopColor: '#3B82F6',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      {text && <span style={{ fontSize: '0.875rem', color: '#94A3B8' }}>{text}</span>}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default LoadingSpinner;
