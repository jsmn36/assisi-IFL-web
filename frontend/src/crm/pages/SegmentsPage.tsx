import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSegments, useSegmentGuests } from '../hooks/useSegments';
import { SegmentCard } from '../components/segments/SegmentCard';
import { GuestTable } from '../components/guest/GuestTable';
import { Pagination } from '../components/shared/Pagination';
import { ErrorCard } from '../components/shared/ErrorCard';
import { useCRMStore } from '../store/crmStore';
import type { SegmentName } from '../types/crm';

import { ArrowLeft } from 'lucide-react';

export default function SegmentsPage() {
  const { name } = useParams<{ name?: string }>();
  const navigate = useNavigate();
  const { data: segments, isLoading, isError } = useSegments();
  const { filters } = useCRMStore();

  const { data: segmentGuests, isError: se } = useSegmentGuests(
    name as SegmentName,
    { page: filters.page }
  );

  if (isError || se) {
    return <ErrorCard message="Could not load segment data." onRetry={() => window.location.reload()} />;
  }

  // Drill-down view
  if (name && segmentGuests) {
    const displayName = name.replace(/_/g, ' ');
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/crm/segments')}
            className="text-gray-400 hover:text-gray-900 flex items-center gap-1 text-sm font-bold"
          >
            <ArrowLeft className="h-4 w-4" />
            BACK TO SEGMENTS
          </button>
        </div>
        <div>
          <h1 style={{ margin: '0 0 4px', fontSize: 22, fontWeight: 700, textTransform: 'capitalize' }}>{displayName} guests</h1>
          <p style={{ margin: '0 0 20px', color: '#6b7280', fontSize: 14 }}>{segmentGuests.total} guests matching this criteria</p>
          <GuestTable guests={segmentGuests.items} />
          <Pagination total={segmentGuests.total} pages={segmentGuests.pages} />
        </div>
      </div>
    );
  }

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
      <div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#111827' }}>Guest Segments</h1>
        <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>Auto-calculated from guest stay history</p>
      </div>

      {isLoading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{ height: 180, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10 }} />
          ))}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {segments?.map(s => <SegmentCard key={s.segment_name} segment={s} />)}
        </div>
      )}
    </div>
  );
}
