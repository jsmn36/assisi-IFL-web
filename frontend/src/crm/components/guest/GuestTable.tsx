import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { CRMGuest } from '../../types/crm';
import { LoyaltyBadge } from './LoyaltyBadge';
import { SegmentTags } from './SegmentTags';
import { EmptyState } from '../shared/EmptyState';
import { SkeletonRow } from '../shared/SkeletonRow';
import { useCRMStore } from '../../store/crmStore';

interface Props {
  guests: CRMGuest[];
  isLoading?: boolean;
}

const COLUMNS = [
  { label: 'Guest',         field: 'name',                   sortable: true  },
  { label: 'Loyalty',       field: '',                        sortable: false },
  { label: 'Segments',      field: '',                        sortable: false },
  { label: 'Stays',         field: 'total_stays_count',       sortable: true  },
  { label: 'Lifetime Rev',  field: 'total_revenue_lifetime',  sortable: true  },
  { label: 'Last Stay',     field: 'last_stay_date',          sortable: true  },
] as const;

export function GuestTable({ guests, isLoading }: Props) {
  const navigate = useNavigate();
  const { filters, setSortField, toggleSortDir } = useCRMStore();

  function handleSort(field: string) {
    if (!field) return;
    const sortField = field as 'name' | 'last_stay_date' | 'total_revenue_lifetime' | 'total_stays_count';
    if (filters.sort_field === sortField) {
      toggleSortDir();
    } else {
      setSortField(sortField);
    }
  }

  function sortIcon(field: string) {
    if (!field || filters.sort_field !== field) return ' ↕';
    return filters.sort_dir === 'asc' ? ' ↑' : ' ↓';
  }

  const thStyle: React.CSSProperties = {
    padding: '10px 14px',
    fontSize: 11,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: '#6b7280',
    textAlign: 'left',
    borderBottom: '1px solid #e5e7eb',
    background: '#f9fafb',
    whiteSpace: 'nowrap',
    userSelect: 'none',
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div style={{ background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody>
            {Array.from({ length: 8 }).map((_, i) => (
              <SkeletonRow key={i} cols={COLUMNS.length} />
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Empty state
  if (!guests.length) {
    return (
      <div style={{
        background: '#fff',
        borderRadius: 8,
        border: '1px solid #e5e7eb',
      }}>
        <EmptyState
          icon="🔍"
          title="No guests found"
          message="Try adjusting your search or clearing the active filters."
        />
      </div>
    );
  }

  return (
    <div style={{
      background: '#fff',
      borderRadius: 8,
      border: '1px solid #e5e7eb',
      overflow: 'hidden',
    }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 640 }}>
          <thead>
            <tr>
              {COLUMNS.map(col => (
                <th
                  key={col.label}
                  style={{
                    ...thStyle,
                    cursor: col.sortable ? 'pointer' : 'default',
                  }}
                  onClick={() => handleSort(col.field)}
                >
                  {col.label}{col.sortable ? sortIcon(col.field) : ''}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {guests.map((guest, idx) => (
              <tr
                key={guest.guest_id}
                onClick={() => navigate(`/crm/guests/${guest.guest_id}`)}
                style={{
                  cursor: 'pointer',
                  background: idx % 2 === 0 ? '#fff' : '#fafafa',
                  transition: 'background 0.1s',
                }}
                onMouseEnter={e =>
                  (e.currentTarget.style.background = '#eff6ff')
                }
                onMouseLeave={e =>
                  (e.currentTarget.style.background =
                    idx % 2 === 0 ? '#fff' : '#fafafa')
                }
              >
                {/* Name + email */}
                <td style={{ padding: '12px 14px' }}>
                  <div style={{ fontWeight: 600, fontSize: 14, color: '#111827' }}>
                    {guest.full_name}
                  </div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                    {guest.email}
                  </div>
                </td>

                {/* Loyalty */}
                <td style={{ padding: '12px 14px' }}>
                  <LoyaltyBadge tier={guest.loyalty_tier} />
                </td>

                {/* Segments */}
                <td style={{ padding: '12px 14px' }}>
                  <SegmentTags segments={guest.segments} />
                </td>

                {/* Stays */}
                <td style={{
                  padding: '12px 14px',
                  fontSize: 14,
                  color: '#374151',
                  textAlign: 'center',
                }}>
                  {guest.total_stays_count}
                </td>

                {/* Revenue */}
                <td style={{
                  padding: '12px 14px',
                  fontSize: 14,
                  color: '#374151',
                  fontWeight: 500,
                }}>
                  ${guest.total_revenue_lifetime.toLocaleString('en-US', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  })}
                </td>

                {/* Last stay */}
                <td style={{ padding: '12px 14px', fontSize: 13, color: '#6b7280' }}>
                  {guest.last_stay_date
                    ? new Date(guest.last_stay_date).toLocaleDateString('en-US', {
                        month: 'short', day: 'numeric', year: 'numeric',
                      })
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
