import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export const Card = ({ children, className }: CardProps) => (
  <div className={cn('bg-white rounded-lg shadow-sm border border-brand-forest-green/10 overflow-hidden hover:shadow-md transition-shadow', className)}>
    {children}
  </div>
);

export const CardHeader = ({ children, className }: CardProps) => (
  <div className={cn('p-6', className)}>{children}</div>
);

export const CardContent = ({ children, className }: CardProps) => (
  <div className={cn('p-6 pt-0', className)}>{children}</div>
);

export const CardFooter = ({ children, className }: CardProps) => (
  <div className={cn('p-6 pt-0 flex items-center', className)}>{children}</div>
);
