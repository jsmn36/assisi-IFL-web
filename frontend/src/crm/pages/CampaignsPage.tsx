import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCampaigns } from '../hooks/useCampaigns';
import { EmptyState } from '../components/shared/EmptyState';
import type { CampaignStatus } from '../types/crm';
import { SEGMENT_META } from '../types/crm';
import { usePermissions } from '../hooks/usePermissions';

const STATUS_STYLES: Record<CampaignStatus, { bg: string; color: string }> = {
  draft:   { bg: '#f3f4f6', color: '#4b5563' },
  sending: { bg: '#fef3c7', color: '#92400e' },
  sent:    { bg: '#d1fae5', color: '#065f46' },
  failed:  { bg: '#fee2e2', color: '#991b1b' },
};

import { ArrowLeft } from 'lucide-react';

export default function CampaignsPage() {
  const navigate = useNavigate();
  const { data: campaigns, isLoading } = useCampaigns();
  const { can } = usePermissions();

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <button 
          onClick={() => window.location.href = '/dashboard'}
          className="text-gray-400 hover:text-gray-900 flex items-center gap-1 text-sm font-bold"
        >
          <ArrowLeft className="h-4 w-4" />
          BACK TO PMS
        </button>
      </div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#111827' }}>Campaigns</h1>
          <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>{campaigns?.length ?? 0} campaigns total</p>
        </div>
        {can('manage_campaigns') && (
          <button 
            onClick={() => navigate('/crm/campaigns/new')} 
            style={{ padding: '9px 18px', background: '#0F2040', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontFamily: 'inherit', fontWeight: 600 }}
          >
            + New Campaign
          </button>
        )}
      </div>

      {isLoading && <div style={{ color: '#6b7280', padding: 20 }}>Loading campaigns…</div>}

      {!isLoading && !campaigns?.length && (
        <div style={{ background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb' }}>
          <EmptyState 
            icon="✉️" 
            title="No campaigns yet" 
            message="Create a campaign to send targeted emails to guest segments." 
            action={can('manage_campaigns') ? { label: 'Create Campaign', onClick: () => navigate('/crm/campaigns/new') } : undefined} 
          />
        </div>
      )}

      {campaigns?.length ? (
        <div style={{ background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, minWidth: 640 }}>
              <thead>
                <tr style={{ background: '#f9fafb' }}>
                  {['Campaign', 'Audience', 'Recipients', 'Status', 'Sent Date'].map(h => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: h === 'Recipients' ? 'center' : 'left', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280', borderBottom: '1px solid #e5e7eb' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {campaigns.map(c => {
                  const s = STATUS_STYLES[c.status];
                  const segMeta = c.segment_name !== 'all' ? SEGMENT_META[c.segment_name] : null;
                  return (
                    <tr key={c.campaign_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '14px 16px', fontWeight: 600 }}>
                        <div style={{ color: '#111827' }}>{c.name}</div>
                        <div style={{ fontSize: 12, color: '#9ca3af', fontWeight: 400, marginTop: 2 }}>{c.subject}</div>
                      </td>
                      <td style={{ padding: '14px 16px', fontSize: 13, color: '#374151' }}>
                        {segMeta ? <span>{segMeta.emoji} {segMeta.label}</span> : 'All Guests'}
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'center', color: '#374151' }}>{c.recipient_count.toLocaleString()}</td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{ 
                          background: s.bg, 
                          color: s.color, 
                          padding: '3px 10px', 
                          borderRadius: 999, 
                          fontSize: 12, 
                          fontWeight: 600,
                          textTransform: 'capitalize' 
                        }}>
                          {c.status}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px', fontSize: 13, color: '#6b7280' }}>
                        {c.sent_at ? new Date(c.sent_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
