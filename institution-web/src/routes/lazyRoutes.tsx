/**
 * Lazy Loaded Routes
 * Handles code splitting for main property management system pages.
 */
import { lazy, Suspense, type ReactNode, type ComponentType } from 'react';
import { RefreshCw } from 'lucide-react';

/**
 * Loading Fallback Component
 * Displayed while the lazy component is being downloaded.
 */
export function LoadingFallback() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4">
      <div className="bg-blue-50/50 p-4 rounded-full">
        <RefreshCw className="h-8 w-8 text-blue-600 animate-spin" />
      </div>
      <p className="text-gray-500 font-medium text-sm">Loading module...</p>
    </div>
  );
}

// Lazy loaded pages with explicit named exports
export const Dashboard = lazy(() => import('@/pages/Dashboard').then(m => ({ default: m.Dashboard })));
export const Reservations = lazy(() => import('@/pages/Reservations').then(m => ({ default: m.Reservations })));
export const Guests = lazy(() => import('@/pages/Guests').then(m => ({ default: m.Guests })));
export const Rooms = lazy(() => import('@/pages/Rooms').then(m => ({ default: m.Rooms })));
export const Reports = lazy(() => import('@/pages/Reports').then(m => ({ default: m.Reports })));
export const UserManagement = lazy(() => import('@/pages/UserManagement').then(m => ({ default: m.UserManagement })));
export const AuditLogs = lazy(() => import('@/pages/AuditLogs').then(m => ({ default: m.AuditLogs })));
export const ComplianceDashboard = lazy(() => import('@/pages/ComplianceDashboard').then(m => ({ default: m.ComplianceDashboard })));
export const GlobalSearch = lazy(() => import('@/pages/GlobalSearch').then(m => ({ default: m.GlobalSearch })));

/**
 * Higher-Order Component with Suspense
 * Wraps a lazy component in a Suspense boundary with the default fallback.
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
