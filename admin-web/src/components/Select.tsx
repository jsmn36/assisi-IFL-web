import { forwardRef } from 'react';
import type { SelectHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: { value: string | number; label: string }[];
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, options, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
);
Select.displayName = 'Select';
export { Select };
