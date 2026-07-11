/**
 * Pull-to-Refresh Component
 * Mobile pull-to-refresh functionality
 */
import { useState, useRef, type ReactNode, type TouchEvent } from 'react';
import { RefreshCw } from 'lucide-react';

interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  children: ReactNode;
  disabled?: boolean;
}

export function PullToRefresh({
  onRefresh,
  children,
  disabled = false,
}: PullToRefreshProps) {
  const [pulling, setPulling] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const startY = useRef(0);
  const currentY = useRef(0);

  const threshold = 80; // Distance to trigger refresh

  const handleTouchStart = (e: TouchEvent) => {
    if (disabled || refreshing) return;

    // Only start if at top of page
    if (window.scrollY === 0) {
      startY.current = e.touches[0].clientY;
      setPulling(true);
    }
  };

  const handleTouchMove = (e: TouchEvent) => {
    if (!pulling || disabled || refreshing) return;

    currentY.current = e.touches[0].clientY;
    const distance = currentY.current - startY.current;

    if (distance > 0) {
      // Prevent pull distance from getting too large too fast
      const resistance = 0.5;
      const actualDistance = Math.min(distance * resistance, threshold * 1.5);
      setPullDistance(actualDistance);
      
      // Prevent default scroll when pulling down
      if (actualDistance > 5) {
        if (e.cancelable) e.preventDefault();
      }
    }
  };

  const handleTouchEnd = async () => {
    if (!pulling || disabled || refreshing) return;

    setPulling(false);

    if (pullDistance >= threshold) {
      setRefreshing(true);
      try {
        await onRefresh();
      } catch (error) {
        console.error('Refresh failed:', error);
      } finally {
        setRefreshing(false);
        setPullDistance(0);
      }
    } else {
      setPullDistance(0);
    }
  };

  const progress = Math.min((pullDistance / threshold) * 100, 100);

  return (
    <div
      className="relative overflow-hidden"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull Indicator */}
      <div
        className="absolute top-0 left-0 right-0 flex items-center justify-center transition-all duration-200 pointer-events-none z-50"
        style={{
          height: `${pullDistance}px`,
          opacity: pullDistance > 0 ? 1 : 0,
        }}
      >
        <div className="bg-white rounded-full p-2 shadow-lg border border-gray-100 flex items-center justify-center">
          <RefreshCw
            className={`h-6 w-6 text-blue-600 ${refreshing ? 'animate-spin' : ''}`}
            style={{
              transform: !refreshing ? `rotate(${progress * 3.6}deg)` : undefined,
            }}
          />
          {!refreshing && (
            <svg className="h-6 w-6 absolute rotate-[-90deg] pointer-events-none">
              <circle
                cx="50%"
                cy="50%"
                r="45%"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="text-blue-100"
              />
              <circle
                cx="50%"
                cy="50%"
                r="45%"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="text-blue-600 transition-all duration-75"
                strokeDasharray="282.6"
                strokeDashoffset={282.6 - (progress / 100) * 282.6}
              />
            </svg>
          )}
        </div>
      </div>

      {/* Content */}
      <div
        style={{
          transform: `translateY(${pullDistance}px)`,
          transition: pulling ? 'none' : 'transform 0.3s ease-out',
        }}
      >
        {children}
      </div>
    </div>
  );
}
