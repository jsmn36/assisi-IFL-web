import React from 'react';
import { SearchBar } from '../components/shared/SearchBar';
import { FilterPanel } from '../components/shared/FilterPanel';
import { GuestTable } from '../components/guest/GuestTable';
import { Pagination } from '../components/shared/Pagination';
import { ErrorCard } from '../components/shared/ErrorCard';
import { useGuests } from '../hooks/useGuests';

import { ArrowLeft } from 'lucide-react';

export default function GuestListPage() {
  const { data, isLoading, isError } = useGuests();

  if (isError) {
    return <ErrorCard message="Could not load guest list." onRetry={() => window.location.reload()} />;
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
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#111827' }}>
          Guests
        </h1>
        <p style={{ margin: '4px 0 0', fontSize: 14, color: '#6b7280' }}>
          {data ? `${data.total.toLocaleString()} guests total` : 'Loading…'}
        </p>
      </div>

      {/* Toolbar */}
      <div style={{
        display: 'flex',
        gap: 12,
        flexWrap: 'wrap',
        alignItems: 'center',
        marginBottom: 16,
      }}>
        <SearchBar />
        <FilterPanel />
      </div>

      {/* Table */}
      <GuestTable
        guests={data?.items ?? []}
        isLoading={isLoading}
      />

      {/* Pagination */}
      {data && (
        <Pagination
          total={data.total}
          pages={data.pages}
        />
      )}
    </div>
  );
}