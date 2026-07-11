import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { useAnalyticsSummary, useLTVBuckets, useRetention } from '../hooks/useAnalytics';
import { SummaryKPIs } from '../components/analytics/SummaryKPIs';
import { LTVChart } from '../components/analytics/LTVChart';
import { RetentionChart } from '../components/analytics/RetentionChart';
import { ErrorCard } from '../components/shared/ErrorCard';

export default function AnalyticsPage() {
  const { data: summary, isLoading: sl, isError: se } = useAnalyticsSummary();
  const { data: ltv,     isLoading: ll, isError: le } = useLTVBuckets();
  const { data: retention, isLoading: rl, isError: re } = useRetention();

  const isLoading = sl || ll || rl;
  const isError   = se || le || re;

  if (isError) {
    return <ErrorCard message="Could not load analytics summary." onRetry={() => window.location.reload()} />;
  }

  if (isLoading) {
    return (
      <div>
        <div style={{ marginBottom: 12, height: 32, width: 140, background: '#e5e7eb', borderRadius: 6 }} />
        <div style={{ marginBottom: 32, height: 16, width: 220, background: '#f3f4f6', borderRadius: 6 }} />
        {/* KPI Skeleton */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12, marginBottom: 24 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ height: 100, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8 }} />
          ))}
        </div>
        {/* Charts Skeleton */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
          <div style={{ height: 300, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8 }} />
          <div style={{ height: 300, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8 }} />
        </div>
      </div>
    );
  }

  if (!summary || !ltv || !retention) return null;

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
      <div className="mb-6">
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#111827' }}>Analytics</h1>
        <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>Guest performance overview</p>
      </div>
      
      <SummaryKPIs data={summary} />
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
        <LTVChart data={ltv} />
        <RetentionChart data={retention} />
      </div>
    </div>
  );
}
