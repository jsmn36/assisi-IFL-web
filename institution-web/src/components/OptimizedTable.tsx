import { memo } from 'react';
import React from 'react';

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (item: T) => React.ReactNode;
}

interface OptimizedTableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (item: T) => string | number;
}

function OptimizedTableComponent<T>({ data, columns, keyExtractor }: OptimizedTableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b">
            {columns.map((column) => (
              <th key={String(column.key)} className="text-left py-3 px-4 font-medium">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={keyExtractor(item)} className="border-b hover:bg-gray-50">
              {columns.map((column) => (
                <td key={String(column.key)} className="py-3 px-4">
                  {column.render ? column.render(item) : String(item[column.key as keyof T])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export const OptimizedTable = memo(OptimizedTableComponent) as typeof OptimizedTableComponent;