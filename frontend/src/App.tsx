import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ToastProvider } from '@/components/Toast';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Login } from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import AdminPanel from '@/pages/AdminPanel';
import PublicFeed from '@/pages/PublicFeed';
import InstitutionProfilePage from '@/pages/InstitutionProfilePage';
import StudentHome from '@/pages/StudentHome';
import StudentProfilePage from '@/pages/StudentProfilePage';
import StudentChat from '@/pages/StudentChat';
import StudentGroups from '@/pages/StudentGroups';
import StudentExplore from '@/pages/StudentExplore';

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: string[];
}

function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-slate-955 flex items-center justify-center text-slate-400">
        Loading session...
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Pages */}
      <Route path="/" element={<PublicFeed />} />
      <Route path="/institutions/:id" element={<InstitutionProfilePage />} />
      <Route path="/login" element={<Login />} />

      {/* Private Educational Institution Dashboard */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute roles={['institution']}>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* Private Super Admin Panel */}
      <Route
        path="/admin-panel"
        element={
          <ProtectedRoute roles={['admin']}>
            <AdminPanel />
          </ProtectedRoute>
        }
      />

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
