import React from 'react';
import type { CRMGuest } from '../../types/crm';
import { LoyaltyBadge } from './LoyaltyBadge';
import { SegmentTags } from './SegmentTags';

export function GuestProfile({ guest }: { guest: CRMGuest }) {
  const stats = [
    { label: 'Total Stays',     value: String(guest.total_stays_count) },
    { label: 'Lifetime Revenue', value: `$${guest.total_revenue_lifetime.toLocaleString()}` },
    { label: 'Avg / Stay',       value: `$${guest.avg_revenue_per_stay.toLocaleString()}` },
    { label: 'Last Stay',        value: guest.last_stay_date
        ? new Date(guest.last_stay_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
        : 'Never' },
  ];

  return (
    <div style={{ background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', padding: 24, marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#111827' }}>{guest.full_name}</h2>
          <div style={{ display: 'flex', gap: 16, marginTop: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, color: '#6b7280' }}>✉ {guest.email}</span>
            {guest.phone && <span style={{ fontSize: 13, color: '#6b7280' }}>📞 {guest.phone}</span>}
            {guest.country && <span style={{ fontSize: 13, color: '#6b7280' }}>🌍 {guest.country}</span>}
          </div>
          <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <LoyaltyBadge tier={guest.loyalty_tier} />
            <SegmentTags segments={guest.segments} />
          </div>
        </div>
        {guest.registration_date && (
          <div style={{ fontSize: 12, color: '#9ca3af' }}>
            Member since {new Date(guest.registration_date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </div>
        )}
      </div>

      {/* Stats row */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1,
        marginTop: 20, background: '#e5e7eb', borderRadius: 6, overflow: 'hidden',
      }}>
        {stats.map(s => (
          <div key={s.label} style={{ background: '#f9fafb', padding: '14px 16px' }}>
            <div style={{ fontSize: 11, color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#111827', marginTop: 2 }}>{s.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
