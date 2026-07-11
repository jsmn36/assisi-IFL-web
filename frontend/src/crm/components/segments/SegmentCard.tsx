import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { SegmentSummary } from '../../types/crm';
import { SEGMENT_META } from '../../types/crm';
import { usePermissions } from '../../hooks/usePermissions';
import { useCRMStore } from '../../store/crmStore';

export function SegmentCard({ segment }: { segment: SegmentSummary }) {
  const navigate  = useNavigate();
  const { can }   = usePermissions();
  const { updateCampaignDraft } = useCRMStore();
  const meta = SEGMENT_META[segment.segment_name];

  function handleSendEmail() {
    updateCampaignDraft({ segment: segment.segment_name });
    navigate('/crm/campaigns/new');
  }

  return (
    <div style={{
      background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10,
      padding: 20, display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 22, marginBottom: 4 }}>{meta.emoji}</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#111827' }}>{meta.label}</div>
          <div style={{ fontSize: 13, color: '#6b7280', marginTop: 2 }}>{meta.description}</div>
        </div>
        <div style={{ fontSize: 28, fontWeight: 800, color: '#0F2040', textAlign: 'right' }}>
          {segment.guest_count}
          <div style={{ fontSize: 11, fontWeight: 400, color: '#9ca3af' }}>guests</div>
        </div>
      </div>

      <div style={{ fontSize: 12, color: '#9ca3af', background: '#f9fafb', padding: '6px 10px', borderRadius: 6 }}>
        Criteria: {meta.criteria}
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <button
          onClick={() => navigate(`/crm/segments/${segment.segment_name}`)}
          style={{ flex: 1, padding: '8px 0', background: '#f3f4f6', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', fontWeight: 500 }}
        >
          View Guests
        </button>
        {can('manage_campaigns') && (
          <button
            onClick={handleSendEmail}
            style={{ flex: 1, padding: '8px 0', background: '#0F2040', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', fontWeight: 500 }}
          >
            Send Email
          </button>
        )}
      </div>
    </div>
  );
}
