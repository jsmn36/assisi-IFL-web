import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ToastProvider } from '@/components/Toast';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import PublicFeed from '@/pages/PublicFeed';
import VisitorLanding from '@/pages/VisitorLanding';
import InstitutionProfilePage from '@/pages/InstitutionProfilePage';

// Lazy-loaded private student social platform pages
const CampusReels = lazy(() => import('@/pages/CampusReels'));
const StudentHome = lazy(() => import('@/pages/StudentHome'));
const StudentProfilePage = lazy(() => import('@/pages/StudentProfilePage'));
const StudentChat = lazy(() => import('@/pages/StudentChat'));
const StudentGroups = lazy(() => import('@/pages/StudentGroups'));
const StudentExplore = lazy(() => import('@/pages/StudentExplore'));

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: string[];
}

function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-slate-900 flex items-center justify-center text-slate-400">
        Loading session...
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/" replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

function ExternalRedirect({ url }: { url: string }) {
  React.useEffect(() => {
    window.location.href = url;
  }, [url]);

  return (
    <div className="h-screen w-screen bg-slate-900 flex items-center justify-center text-slate-400">
      Redirecting to portal...
    </div>
  );
}

function PageLoading() {
  return (
    <div className="h-screen w-screen bg-slate-950 flex items-center justify-center text-slate-400 text-sm font-semibold">
      Loading page...
    </div>
  );
}

function AppRoutes() {
  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
        {/* Public Pages */}
        <Route path="/" element={<VisitorLanding />} />
        <Route path="/public-feed" element={<PublicFeed />} />
        <Route path="/notes" element={<PublicFeed />} />
        <Route path="/reels" element={<CampusReels />} />
        <Route path="/institutions/:id" element={<InstitutionProfilePage />} />
        <Route path="/login" element={<Navigate to="/" replace />} />

        {/* External Portal Redirects */}
        <Route path="/dashboard" element={<ExternalRedirect url="http://localhost:3002" />} />
        <Route path="/admin-panel" element={<ExternalRedirect url="http://localhost:3001" />} />

        {/* Private Student Social Platform Pages */}
        <Route
          path="/student-home"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentHome />
            </ProtectedRoute>
          }
        />
        <Route
          path="/students/profile/:username"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentChat />
            </ProtectedRoute>
          }
        />
        <Route
          path="/classrooms"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentGroups />
            </ProtectedRoute>
          }
        />
        <Route
          path="/explore"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentExplore />
            </ProtectedRoute>
          }
        />

        {/* Fallbacks */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <BrowserRouter>
          <AuthProvider>
            <ToastProvider>
              <AppRoutes />
            </ToastProvider>
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
