/**
 * Skeleton primitives for loading states.
 *
 * Use a Skeleton block while waiting on data instead of a blank screen
 * or a spinner — the layout shifts less when real content arrives, and
 * users get an immediate sense of "something's coming".
 */
import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      aria-busy="true"
      aria-live="polite"
      className={cn('animate-pulse rounded-md bg-gray-200', className)}
      {...props}
    />
  );
}

export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn('h-3', i === lines - 1 ? 'w-2/3' : 'w-full')}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'rounded-lg border border-gray-200 bg-white p-4 shadow-sm space-y-3',
        className
      )}
    >
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <SkeletonText lines={2} />
    </div>
  );
}

export function SkeletonTable({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
      <div className="grid gap-2 p-4 border-b border-gray-200" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div
          key={r}
          className="grid gap-2 p-4 border-b border-gray-100 last:border-b-0"
          style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
        >
          {Array.from({ length: columns }).map((_, c) => (
            <Skeleton key={c} className="h-3" />
          ))}
        </div>
      ))}
    </div>
  );
}

/** A handy pre-composed dashboard placeholder. */
export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
      <SkeletonTable rows={6} columns={5} />
    </div>
  );
}
