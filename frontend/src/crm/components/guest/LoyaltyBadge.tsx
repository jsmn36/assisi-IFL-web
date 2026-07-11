import React from 'react';
import type { LoyaltyTier } from '../../types/crm';

const TIER_STYLES: Record<LoyaltyTier, { bg: string; color: string }> = {
  platinum: { bg: '#e5e7eb', color: '#1f2937' },
  gold:     { bg: '#fef3c7', color: '#92400e' },
  silver:   { bg: '#f3f4f6', color: '#4b5563' },
  bronze:   { bg: '#fde8d8', color: '#9a3412' },
};

export function LoyaltyBadge({ tier }: { tier: LoyaltyTier | null }) {
  if (!tier) {
    return <span style={{ color: '#d1d5db', fontSize: 12 }}>—</span>;
  }

  const s = TIER_STYLES[tier];

  return (
    <span style={{
      background: s.bg,
      color: s.color,
      padding: '2px 8px',
      borderRadius: 999,
      fontSize: 11,
      fontWeight: 600,
      textTransform: 'capitalize',
    }}>
      {tier}
    </span>
  );
}
