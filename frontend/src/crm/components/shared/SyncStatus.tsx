import React, { useEffect, useState } from 'react';
import { crmSyncApi } from '../../api/crmClient';
import type { SyncStatusRecord } from '../../types/crm';

/**
 * SyncStatus Component
 * Displays the current synchronization status between the PMS and CRM.
 */
export const SyncStatus = () => {
  const [status, setStatus] = useState<SyncStatusRecord | null>(null);

  useEffect(() => {
    // Phase 1: Fetch mock sync status
    crmSyncApi.status().then(setStatus).catch(console.error);
    
    // Refresh every minute
    const interval = setInterval(() => {
      crmSyncApi.status().then(setStatus).catch(console.error);
    }, 60000);
    
    return () => clearInterval(interval);
  }, []);

  if (!status) return null;

  const statusConfig = {
    success: { bg: '#d1fae5', color: '#065f46', label: 'Synced' },
    running: { bg: '#fef3c7', color: '#92400e', label: 'Syncing...' },
    error:   { bg: '#fee2e2', color: '#991b1b', label: 'Sync Error' },
    never:   { bg: '#f3f4f6', color: '#374151', label: 'Not Synced' },
  }[status.status] || { bg: '#f3f4f6', color: '#374151', label: status.status };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div 
        title={status.last_error || undefined}
        style={{
          fontSize: 12,
          background: statusConfig.bg,
          color: statusConfig.color,
          padding: '4px 12px',
          borderRadius: 999,
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
        }}
      >
        <span style={{ 
          width: 6, 
          height: 6, 
          borderRadius: '50%', 
          background: statusConfig.color,
          opacity: status.status === 'running' ? 0.5 : 1
        }} />
        {statusConfig.label}
      </div>
      
      {status.last_sync_at && (
        <span style={{ fontSize: 11, color: '#9ca3af', fontWeight: 400 }}>
          Last sync: {new Date(status.last_sync_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      )}
    </div>
  );
};