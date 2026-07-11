import React from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && <label className="text-sm font-medium text-brand-charcoal">{label}</label>}
        <input
          ref={ref}
          className={cn(
            'flex h-10 w-full rounded-md border border-brand-warm-gray/30 bg-transparent px-3 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-brand-warm-gray focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-forest-green focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-brand-error focus-visible:ring-brand-error',
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-brand-error">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
