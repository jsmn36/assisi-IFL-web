import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ToastProvider } from '@/components/Toast';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Login } from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';

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
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute roles={['institution']}>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
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
