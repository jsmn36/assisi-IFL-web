import React from 'react';

interface Props { 
  message?: string; 
  onRetry?: () => void; 
}

/**
 * ErrorCard component
 * Displays a user-friendly error message with an optional retry action.
 */
export function ErrorCard({ message = 'Something went wrong while loading data.', onRetry }: Props) {
  return (
    <div style={{ padding: '32px 24px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 10, textAlign: 'center' }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
      <div style={{ fontWeight: 700, fontSize: 16, color: '#991b1b', marginBottom: 4 }}>Error</div>
      <p style={{ margin: '0 0 16px', fontSize: 14, color: '#b91c1c', maxWidth: 300, marginLeft: 'auto', marginRight: 'auto' }}>
        {message}
      </p>
      {onRetry && (
        <button 
          onClick={onRetry} 
          style={{ 
            padding: '9px 20px', 
            background: '#991b1b', 
            color: '#fff', 
            border: 'none', 
            borderRadius: 7, 
            cursor: 'pointer', 
            fontFamily: 'inherit', 
            fontSize: 13,
            fontWeight: 600,
            boxShadow: '0 2px 4px rgba(153, 27, 27, 0.2)',
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
