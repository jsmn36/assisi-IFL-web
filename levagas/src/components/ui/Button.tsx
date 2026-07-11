import React from 'react';
import { cn } from '@/lib/utils'; // I'll create this helper next

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'cta-large';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', isLoading, children, disabled, ...props }, ref) => {
    const variants = {
      primary: 'bg-brand-forest-green text-white border-2 border-brand-forest-green hover:bg-brand-deep-green',
      secondary: 'bg-transparent text-brand-forest-green border-2 border-brand-forest-green hover:bg-brand-forest-green hover:text-white',
      ghost: 'bg-transparent text-brand-forest-green hover:bg-brand-forest-green/10',
      'cta-large': 'bg-brand-forest-green text-white border-2 border-brand-forest-green hover:bg-brand-deep-green px-8 py-4 text-lg font-semibold',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center rounded-md px-6 py-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-forest-green disabled:opacity-50 disabled:pointer-events-none',
          variants[variant],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : null}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
