import React from 'react';

/**
 * SkeletonRow component
 * Displays a single row with shimmering skeleton placeholders for loading tables.
 */
export function SkeletonRow({ cols = 6 }: { cols?: number }) {
  return (
    <tr style={{ background: '#fff' }}>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} style={{ padding: '13px 14px', borderBottom: '1px solid #f3f4f6' }}>
          <div style={{
            height: 14, 
            borderRadius: 4,
            backgroundImage: 'linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%)',
            backgroundSize: '200% 100%',
            animation: 'shimmer 2s infinite linear',
            width: i === 0 ? '70%' : i === 1 ? '40%' : '60%',
          }} />
        </td>
      ))}
    </tr>
  );
}
