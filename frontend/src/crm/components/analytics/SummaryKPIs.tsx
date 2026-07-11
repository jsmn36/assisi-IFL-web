import React from 'react';
import type { AnalyticsSummary } from '../../types/crm';

interface KPI { label: string; value: string; sub?: string; color: string }

export function SummaryKPIs({ data }: { data: AnalyticsSummary }) {
  const kpis: KPI[] = [
    { label: 'Total Guests',      value: data.total_guests.toLocaleString(),                     color: '#0F2040' },
    { label: 'Repeat Guest Rate', value: `${Math.round(data.repeat_guest_rate * 100)}%`,          sub: '2+ stays',               color: '#059669' },
    { label: 'Avg Lifetime Value', value: `$${data.avg_ltv.toLocaleString()}`,                    sub: 'per guest',              color: '#d97706' },
    { label: 'Avg Stays / Guest', value: data.avg_stays_per_guest.toFixed(1),                     color: '#7c3aed' },
    { label: 'Active Campaigns',  value: String(data.active_campaigns),                           sub: 'in draft',               color: '#db2777' },
    { label: 'Synced Today',      value: String(data.guests_synced_today),                        sub: 'records updated',        color: '#0891b2' },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12, marginBottom: 24 }}>
      {kpis.map(k => (
        <div key={k.label} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '16px 18px' }}>
          <div style={{ fontSize: 11, color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>{k.label}</div>
          <div style={{ fontSize: 26, fontWeight: 800, color: k.color }}>{k.value}</div>
          {k.sub && <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>{k.sub}</div>}
        </div>
      ))}
    </div>
  );
}
