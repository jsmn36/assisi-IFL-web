import { useCRMStore } from '../../store/crmStore';
import type { SegmentName, LoyaltyTier } from '../../types/crm';

const SEGMENT_OPTIONS: { value: SegmentName | 'all'; label: string }[] = [
  { value: 'all',          label: 'All Segments' },
  { value: 'vip',          label: '💎 VIP' },
  { value: 'repeat',       label: '🔁 Repeat' },
  { value: 'first_time',   label: '🆕 First-Time' },
  { value: 'inactive',     label: '😴 Inactive' },
  { value: 'high_spender', label: '💰 High Spenders' },
  { value: 'frequent',     label: '⭐ Frequent' },
];

const TIER_OPTIONS: { value: LoyaltyTier | 'all'; label: string }[] = [
  { value: 'all',      label: 'All Tiers' },
  { value: 'platinum', label: 'Platinum' },
  { value: 'gold',     label: 'Gold' },
  { value: 'silver',   label: 'Silver' },
  { value: 'bronze',   label: 'Bronze' },
];

const SORT_OPTIONS: { value: string; label: string }[] = [
  { value: 'last_stay_date',          label: 'Last Stay (newest)' },
  { value: 'total_revenue_lifetime',  label: 'Revenue (highest)' },
  { value: 'total_stays_count',       label: 'Stays (most)' },
  { value: 'name',                    label: 'Name (A–Z)' },
];

const selectStyle: React.CSSProperties = {
  padding: '7px 10px',
  border: '1px solid #d1d5db',
  borderRadius: 6,
  fontSize: 13,
  background: '#fff',
  cursor: 'pointer',
  fontFamily: 'inherit',
  outline: 'none',
};

export function FilterPanel() {
  const {
    filters,
    setSegmentFilter,
    setLoyaltyTierFilter,
    setSortField,
    resetFilters,
  } = useCRMStore();

  const hasActiveFilters =
    filters.segment !== null ||
    filters.loyalty_tier !== null ||
    filters.search !== '';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>

      {/* Segment */}
      <select
        style={selectStyle}
        value={filters.segment ?? 'all'}
        onChange={(e) => {
          const v = e.target.value;
          setSegmentFilter(v === 'all' ? null : (v as SegmentName));
        }}
      >
        {SEGMENT_OPTIONS.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>

      {/* Loyalty tier */}
      <select
        style={selectStyle}
        value={filters.loyalty_tier ?? 'all'}
        onChange={(e) => {
          const v = e.target.value;
          setLoyaltyTierFilter(v === 'all' ? null : (v as LoyaltyTier));
        }}
      >
        {TIER_OPTIONS.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>

      {/* Sort */}
      <select
        style={selectStyle}
        value={filters.sort_field}
        onChange={(e) =>
          setSortField(e.target.value as typeof filters.sort_field)
        }
      >
        {SORT_OPTIONS.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>

      {/* Clear filters — only shows when something is active */}
      {hasActiveFilters && (
        <button
          onClick={resetFilters}
          style={{
            padding: '7px 12px',
            background: 'transparent',
            border: '1px solid #e5e7eb',
            borderRadius: 6, fontSize: 13,
            cursor: 'pointer', color: '#6b7280',
            fontFamily: 'inherit',
          }}
        >
          Clear filters
        </button>
      )}
    </div>
  );
}