/**
 * Lazy Loaded Routes
 * Handles code splitting for Assisi Social portal pages.
 */
import { lazy, Suspense, type ComponentType } from 'react';
import { RefreshCw } from 'lucide-react';

/**
 * Loading Fallback Component
 */
export function LoadingFallback() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4">
      <div className="bg-indigo-50/50 p-4 rounded-full">
        <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin" />
      </div>
      <p className="text-gray-500 font-medium text-sm">Loading module...</p>
    </div>
  );
}

// Lazy loaded pages with default exports
export const PublicFeed = lazy(() => import('@/pages/PublicFeed'));
export const VisitorLanding = lazy(() => import('@/pages/VisitorLanding'));
export const StudentHome = lazy(() => import('@/pages/StudentHome'));

/**
 * Higher-Order Component with Suspense
 */
export function withSuspense<T extends object>(Component: ComponentType<T>) {
  return function WrappedComponent(props: T) {
    return (
      <Suspense fallback={<LoadingFallback />}>
        <Component {...props} />
      </Suspense>
    );
  };
}
