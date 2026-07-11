import React from 'react';
import type { SegmentName } from '../../types/crm';
import { SEGMENT_META } from '../../types/crm';

export function SegmentTags({ segments }: { segments: SegmentName[] }) {
  if (!segments.length) return null;

  return (
    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
      {segments.map(s => (
        <span
          key={s}
          title={SEGMENT_META[s]?.criteria || ''}
          style={{
            fontSize: 10,
            padding: '2px 6px',
            borderRadius: 999,
            background: '#f0f4ff',
            color: '#3730a3',
            fontWeight: 500,
            whiteSpace: 'nowrap',
          }}
        >
          {SEGMENT_META[s]?.emoji || '🏷️'} {SEGMENT_META[s]?.label || s}
        </span>
      ))}
    </div>
  );
}
