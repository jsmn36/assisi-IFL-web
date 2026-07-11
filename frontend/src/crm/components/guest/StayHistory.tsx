import React from 'react';
import type { CRMStay } from '../../types/crm';
import { EmptyState } from '../shared/EmptyState';

export function StayHistory({ stays }: { stays: CRMStay[] }) {
  if (!stays.length) {
    return <EmptyState icon="🏨" title="No stays recorded" message="Stay history will appear here once synced from PMS." />;
  }

  const sorted = [...stays].sort(
    (a, b) => new Date(b.check_in_date).getTime() - new Date(a.check_in_date).getTime()
  );

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, minWidth: 720 }}>
        <thead>
          <tr style={{ background: '#f9fafb' }}>
            {['Check-in', 'Check-out', 'Room', 'Nights', 'Room Rev', 'Other Rev', 'Total', 'Status'].map(h => (
              <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6b7280', borderBottom: '1px solid #e5e7eb' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(stay => (
            <tr key={stay.stay_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
              <td style={{ padding: '11px 14px', color: '#374151' }}>
                {new Date(stay.check_in_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </td>
              <td style={{ padding: '11px 14px', color: '#374151' }}>
                {new Date(stay.check_out_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </td>
              <td style={{ padding: '11px 14px', fontWeight: 600 }}>{stay.room_number ?? '—'}</td>
              <td style={{ padding: '11px 14px', textAlign: 'center' }}>{stay.nights}</td>
              <td style={{ padding: '11px 14px' }}>${stay.room_revenue.toLocaleString()}</td>
              <td style={{ padding: '11px 14px' }}>${stay.other_revenue.toLocaleString()}</td>
              <td style={{ padding: '11px 14px', fontWeight: 700, color: '#111827' }}>${stay.total_revenue.toLocaleString()}</td>
              <td style={{ padding: '11px 14px' }}>
                <span style={{
                  fontSize: 11, padding: '2px 8px', borderRadius: 999,
                  background: stay.status === 'active' ? '#d1fae5' : '#f3f4f6',
                  color: stay.status === 'active' ? '#065f46' : '#6b7280',
                  fontWeight: 600,
                }}>
                  {stay.status === 'active' ? 'Active' : 'Checked Out'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
