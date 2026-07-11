import React from 'react';
import { cn } from '@/lib/utils';

interface SectionProps {
  children: React.ReactNode;
  className?: string;
  containerClassName?: string;
  id?: string;
  background?: 'primary' | 'white' | 'forest';
}

export const Section = ({
  children,
  className,
  containerClassName,
  id,
  background = 'white'
}: SectionProps) => {
  const bgStyles = {
    primary: 'bg-brand-primary-bg',
    white: 'bg-brand-cream-white',
    forest: 'bg-brand-forest-green text-white',
  };

  return (
    <section
      id={id}
      className={cn('py-16 md:py-24', bgStyles[background], className)}
    >
      <div className={cn('max-w-7xl mx-auto px-6', containerClassName)}>
        {children}
      </div>
    </section>
  );
};
