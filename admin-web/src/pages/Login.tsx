import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Label } from '@/components/Label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { AlertCircle, Lock, User as UserIcon, ShieldAlert, Building } from 'lucide-react';

const loginSchema = z.object({
  username: z.string().trim().min(1, 'Username or email is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function Login() {
  const { login, isAuthenticated, pendingMemberships, user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [serverError, setServerError] = useState('');

  const loginForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });

  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'admin') {
        navigate('/admin-panel', { replace: true });
      } else {
        // Non-admin session detected (e.g. student or institution); clear session to allow admin login
        logout();
      }
    }
  }, [isAuthenticated, user, navigate, logout]);

  if (pendingMemberships.length > 0 && user?.role === 'admin') {
    navigate('/admin-panel', { replace: true });
  }

  const onLoginSubmit = async (values: LoginFormValues) => {
    setServerError('');
    try {
      await login(values.username, values.password);
    } catch (err) {
      const message =
        (err as { error?: string; detail?: string; message?: string } | null)?.error ??
        (err as { detail?: string } | null)?.detail ??
        (err as Error | null)?.message ??
        'Login failed. Please check your credentials.';
      setServerError(message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4 py-8 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-rose-600 rounded-full blur-[120px] opacity-15 pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[45%] h-[45%] bg-slate-500 rounded-full blur-[120px] opacity-15 pointer-events-none"></div>

      <Card className="w-full max-w-md bg-slate-800/80 border-slate-700/50 backdrop-blur-xl text-slate-100 shadow-2xl relative z-10 animate-fade-in">
        <CardHeader className="text-center pb-4">
          <div className="mx-auto h-14 w-auto bg-white p-1.5 rounded-2xl flex items-center justify-center mb-3 shadow-lg shadow-rose-500/20">
            <img src="/logo.png" alt="ASSISI IFL Logo" className="h-10 w-auto object-contain" />
          </div>
          <CardTitle className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-rose-200 to-rose-400 bg-clip-text text-transparent">
            Super Admin
          </CardTitle>
          <p className="text-sm text-slate-400 mt-1">
            Assisi Social Platform Control Center
          </p>
        </CardHeader>
        <CardContent>
          {serverError && (
            <div
              role="alert"
              className="flex items-start gap-2.5 p-3.5 mb-4 bg-red-950/50 border border-red-500/30 rounded-xl text-red-300 text-sm"
            >
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-red-400" />
              <span>{serverError}</span>
            </div>
          )}

          <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-4" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="username" className="text-slate-300">Super Admin Username</Label>
              <div className="relative">
                <UserIcon className="absolute left-3.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="username"
                  type="text"
                  placeholder="admin"
                  className="pl-10 bg-slate-900/60 border-slate-700/60 focus:border-rose-500 focus:ring-rose-500/20 text-white"
                  autoFocus
                  disabled={loginForm.formState.isSubmitting}
                  {...loginForm.register('username')}
                />
              </div>
              {loginForm.formState.errors.username && (
                <p className="text-xs text-red-400 font-medium">{loginForm.formState.errors.username.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-slate-300">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  className="pl-10 bg-slate-900/60 border-slate-700/60 focus:border-rose-500 focus:ring-rose-500/20 text-white"
                  disabled={loginForm.formState.isSubmitting}
                  {...loginForm.register('password')}
                />
              </div>
              {loginForm.formState.errors.password && (
                <p className="text-xs text-red-400 font-medium">{loginForm.formState.errors.password.message}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 py-2.5 font-bold shadow-lg shadow-rose-600/15"
              disabled={loginForm.formState.isSubmitting}
            >
              {loginForm.formState.isSubmitting ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-5 pt-4 border-t border-slate-700/40 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <a
                href="http://localhost:3002"
                className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Building className="h-4 w-4" />
                <span>Branch Space Login</span>
              </a>
              <a
                href="http://localhost:3000"
                className="text-slate-400 hover:text-white transition-colors inline-flex items-center gap-1"
              >
                <span>&larr; Return to Visitor Homepage</span>
              </a>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
