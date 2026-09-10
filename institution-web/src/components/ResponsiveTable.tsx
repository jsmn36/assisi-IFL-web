import React from 'react';
import { useIsMobile } from '@/hooks/useMediaQuery';

interface Column {
  key: string;
  label: string;
  render?: (value: any, row: any) => React.ReactNode;
  mobileLabel?: string;
  hideOnMobile?: boolean;
}

interface ResponsiveTableProps {
  columns: Column[];
  data: any[];
  onRowClick?: (row: any) => void;
  loading?: boolean;
  emptyMessage?: string;
}

/**
 * Responsive Table Component
 * Transforms from a desktop row-based table to a mobile-friendly card view automatically.
 */
export function ResponsiveTable({
  columns,
  data,
  onRowClick,
  loading,
  emptyMessage = 'No data available',
}: ResponsiveTableProps) {
  const isMobile = useIsMobile();

  // Loading skeleton using CSS animations
  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-16 w-full bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  // Handle empty datasets
  if (data.length === 0) {
    return (
      <div className="py-12 text-center text-gray-500 bg-gray-50 rounded-lg border border-dashed">
        {emptyMessage}
      </div>
    );
  }

  // Mobile Card View: Stacks fields vertically for narrow screens
  if (isMobile) {
    return (
      <div className="space-y-3">
        {data.map((row, index) => (
          <div
            key={index}
            onClick={() => onRowClick?.(row)}
            className={`bg-white rounded-xl border p-4 shadow-sm active:scale-[0.98] transition-transform ${ 
              onRowClick ? 'cursor-pointer active:bg-gray-50' : '' 
            }`}
          >
            {columns
              .filter(col => !col.hideOnMobile)
              .map((col) => (
                <div key={col.key} className="flex justify-between py-1.5 border-b border-gray-50 last:border-0">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-tight">
                    {col.mobileLabel || col.label}
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </span>
                </div>
              ))}
          </div>
        ))}
      </div>
    );
  }

  // Desktop Table View: Standard data grid with hover effects
  return (
    <div className="overflow-hidden border rounded-xl bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[700px]">
          <thead>
            <tr className="bg-gray-50">
              {columns.map((col) => (
                <th key={col.key} className="px-6 py-4 text-xs font-bold text-gray-600 uppercase tracking-wider">
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((row, index) => (
              <tr
                key={index}
                onClick={() => onRowClick?.(row)}
                className={`transition-colors ${onRowClick ? 'hover:bg-blue-50/30 cursor-pointer' : ''}`}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
