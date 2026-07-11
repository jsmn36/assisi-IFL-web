// @ts-nocheck
import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import type { RetentionPoint } from '../../types/crm';

export function RetentionChart({ data }: { data: RetentionPoint[] }) {
  const formatted = data.map(d => ({
    ...d,
    month: new Date(d.month + '-01').toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
    pct: Math.round(d.repeat_rate * 100),
  }));

  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 20 }}>
      <h3 style={{ margin: '0 0 16px', fontSize: 15, fontWeight: 600 }}>Repeat Guest Rate (Monthly)</h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={formatted} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} tickFormatter={v => `${v}%`} domain={[0, 100]} />
          <Tooltip 
            formatter={(v: number) => [`${v}%`, 'Repeat Rate']} 
            contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
          />
          <Line type="monotone" dataKey="pct" stroke="#F59E0B" strokeWidth={2.5} dot={{ r: 4, fill: '#F59E0B', strokeWidth: 2, stroke: '#fff' }} activeDot={{ r: 6 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
