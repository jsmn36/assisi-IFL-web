/**
 * Mobile Card Component
 * Touch-friendly card with swipe actions
 */
import { type ReactNode } from 'react';
import { useSwipe } from '@/hooks/useSwipe';
import { ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MobileCardProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  onClick?: () => void;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  badge?: ReactNode;
  avatar?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function MobileCard({
  title,
  subtitle,
  children,
  onClick,
  onSwipeLeft,
  onSwipeRight,
  badge,
  avatar,
  actions,
  className,
}: MobileCardProps) {
  const swipeHandlers = useSwipe({
    onSwipeLeft,
    onSwipeRight,
    minSwipeDistance: 100,
  });

  return (
    <div
      {...swipeHandlers}
      onClick={onClick}
      className={cn(
        'bg-white rounded-lg border p-4 flex items-center transition-colors',
        onClick ? 'cursor-pointer active:bg-gray-100' : '',
        className
      )}
    >
      {avatar && (
        <div className="flex-shrink-0 mr-3">
          {avatar}
        </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-medium text-base truncate">{title}</h3>
          {badge && <div className="flex-shrink-0 ml-2">{badge}</div>}
        </div>
        
        {subtitle && (
          <p className="text-sm text-gray-600 truncate">{subtitle}</p>
        )}
        
        {children && <div className="mt-3">{children}</div>}
      </div>

      {onClick && !actions && (
        <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0 ml-2" />
      )}
      
      {actions && (
        <div className="flex-shrink-0 ml-2">
          {actions}
        </div>
      )}
    </div>
  );
}
