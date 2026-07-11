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
import { AlertCircle, Lock, User as UserIcon, Mail, BookOpen, GraduationCap, CheckCircle } from 'lucide-react';
import api from '@/lib/api';

const loginSchema = z.object({
  username: z.string().trim().min(1, 'Username or email is required'),
  password: z.string().min(1, 'Password is required'),
});

const registerSchema = z.object({
  admission_number: z.string().trim().min(1, 'Admission number is required'),
  username: z.string().trim().min(3, 'Username must be at least 3 characters'),
  email: z.string().trim().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  first_name: z.string().trim().min(1, 'First name is required'),
  last_name: z.string().trim().min(1, 'Last name is required'),
  class_or_department: z.string().trim().optional(),
});

type LoginFormValues = z.infer<typeof loginSchema>;
type RegisterFormValues = z.infer<typeof registerSchema>;

export function Login() {
  const { login, isAuthenticated, pendingMemberships, user } = useAuth();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  const [serverError, setServerError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [registering, setRegistering] = useState(false);

  const loginForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });

  const registerForm = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      admission_number: '',
      username: '',
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      class_or_department: '',
    },
  });

  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'admin') {
        navigate('/admin-panel', { replace: true });
      } else if (user.role === 'student') {
        navigate('/student-home', { replace: true });
      } else {
        navigate('/dashboard', { replace: true });
      }
    }
  }, [isAuthenticated, user, navigate]);

  if (pendingMemberships.length > 0) {
    navigate('/dashboard', { replace: true });
  }

  const onLoginSubmit = async (values: LoginFormValues) => {
    setServerError('');
    setSuccessMessage('');
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

  const onRegisterSubmit = async (values: RegisterFormValues) => {
    setServerError('');
    setSuccessMessage('');
    setRegistering(true);
    try {
      await api.registerStudent(values);
      setSuccessMessage('Registration submitted! Your account is pending institutional review and approval.');
      registerForm.reset();
      setActiveTab('login');
    } catch (err) {
      const message =
        (err as { error?: string; detail?: string; message?: string } | null)?.error ??
        (err as { detail?: string } | null)?.detail ??
        (err as Error | null)?.message ??
        'Registration failed. Please check details.';
      setServerError(message);
    } finally {
      setRegistering(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4 py-8 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-violet-600 rounded-full blur-[120px] opacity-20 pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[45%] h-[45%] bg-indigo-500 rounded-full blur-[120px] opacity-20 pointer-events-none"></div>

      <Card className="w-full max-w-md bg-slate-800/80 border-slate-700/50 backdrop-blur-xl text-slate-100 shadow-2xl relative z-10">
        <CardHeader className="text-center pb-4">
          <div className="mx-auto h-12 w-12 bg-indigo-500/10 rounded-xl flex items-center justify-center mb-3 border border-indigo-500/20">
            <GraduationCap className="h-6 w-6 text-indigo-400" />
          </div>
          <CardTitle className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
            Assisi Social
          </CardTitle>
          <p className="text-sm text-slate-400 mt-1">
            Connect. Learn. Share. Student Social Hub.
          </p>
        </CardHeader>
        <CardContent>
          {/* Tabs */}
          <div className="grid grid-cols-2 bg-slate-950/40 p-1 rounded-xl mb-6 border border-slate-700/30">
            <button
              onClick={() => {
                setActiveTab('login');
                setServerError('');
                setSuccessMessage('');
              }}
              className={`py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
                activeTab === 'login'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setActiveTab('register');
                setServerError('');
                setSuccessMessage('');
              }}
              className={`py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
                activeTab === 'register'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Student Register
            </button>
          </div>

          {serverError && (
            <div
              role="alert"
              className="flex items-start gap-2.5 p-3.5 mb-4 bg-red-950/50 border border-red-500/30 rounded-xl text-red-300 text-sm"
            >
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-red-400" />
              <span>{serverError}</span>
            </div>
          )}

          {successMessage && (
            <div
              role="alert"
              className="flex items-start gap-2.5 p-3.5 mb-4 bg-emerald-950/50 border border-emerald-500/30 rounded-xl text-emerald-300 text-sm"
            >
              <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-emerald-400" />
              <span>{successMessage}</span>
            </div>
          )}

          {activeTab === 'login' ? (
            <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-4" noValidate>
              <div className="space-y-1.5">
                <Label htmlFor="username" className="text-slate-300">Username or Email</Label>
                <div className="relative">
                  <UserIcon className="absolute left-3.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="username"
                    type="text"
                    placeholder="Enter your username"
                    className="pl-10 bg-slate-900/60 border-slate-700/60 focus:border-indigo-500 focus:ring-indigo-500/20 text-white"
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
                    placeholder="Enter your password"
                    className="pl-10 bg-slate-900/60 border-slate-700/60 focus:border-indigo-500 focus:ring-indigo-500/20 text-white"
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
                className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 py-2.5 font-bold shadow-lg shadow-indigo-600/15"
                disabled={loginForm.formState.isSubmitting}
              >
                {loginForm.formState.isSubmitting ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
          ) : (
            <form onSubmit={registerForm.handleSubmit(onRegisterSubmit)} className="space-y-3.5" noValidate>
              <div className="space-y-1.5">
                <Label htmlFor="admission_number" className="text-slate-300">Admission Number *</Label>
                <div className="relative">
                  <BookOpen className="absolute left-3.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="admission_number"
                    type="text"
                    placeholder="e.g. 2026-001"
                    className="pl-10 bg-slate-900/60 border-slate-700/60 focus:border-indigo-500 focus:ring-indigo-500/20 text-white"
                    disabled={registering}
                    {...registerForm.register('admission_number')}
                  />
                </div>
                {registerForm.formState.errors.admission_number && (
                  <p className="text-xs text-red-400 font-medium">{registerForm.formState.errors.admission_number.message}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="first_name" className="text-slate-300">First Name *</Label>
                  <Input
                    id="first_name"
                    type="text"
                    placeholder="First Name"
                    className="bg-slate-900/60 border-slate-700/60 text-white"
                    disabled={registering}
                    {...registerForm.register('first_name')}
                  />
                  {registerForm.formState.errors.first_name && (
                    <p className="text-xs text-red-400 font-medium">{registerForm.formState.errors.first_name.message}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="last_name" className="text-slate-300">Last Name *</Label>
                  <Input
                    id="last_name"
                    type="text"
                    placeholder="Last Name"
                    className="bg-slate-900/60 border-slate-700/60 text-white"
                    disabled={registering}
                    {...registerForm.register('last_name')}
                  />
                  {registerForm.formState.errors.last_name && (
                    <p className="text-xs text-red-400 font-medium">{registerForm.formState.errors.last_name.message}</p>
                  )}
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="reg_username" className="text-slate-300">Username *</Label>
                <div className="relative">
                  <UserIcon className="absolute left-3.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="reg_username"
                    type="text"
                    placeholder="Choose a username"
                    className="pl-10 bg-slate-900/60 border-slate-700/60 focus:border-indigo-500 focus:ring-indigo-500/20 text-white"
                    disabled={registering}
                    {...registerForm.register('username')}
                  />
                </div>
                {registerForm.formState.errors.username && (
                  <p className="text-xs text-red-400 font-medium">{registerForm.formState.errors.username.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="reg_email" className="text-slate-300">Email Address *</Label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="reg_email"
                    type="email"
                    placeholder="email@assisi.edu"
                    className="pl-10 bg-slate-900/60 border-slate-700/60 focus:border-indigo-500 focus:ring-indigo-500/20 text-white"
                    disabled={registering}
                    {...registerForm.register('email')}
                  />
                </div>
                {registerForm.formState.errors.email && (
                  <p className="text-xs text-red-400 font-medium">{registerForm.formState.errors.email.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="reg_password" className="text-slate-300">Password *</Label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="reg_password"
                    type="password"
                    placeholder="Choose a password"
                    className="pl-10 bg-slate-900/60 border-slate-700/60 focus:border-indigo-500 focus:ring-indigo-500/20 text-white"
                    disabled={registering}
                    {...registerForm.register('password')}
                  />
                </div>
                {registerForm.formState.errors.password && (
                  <p className="text-xs text-red-400 font-medium">{registerForm.formState.errors.password.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="class_or_department" className="text-slate-300">Department / Class</Label>
                <Input
                  id="class_or_department"
                  type="text"
                  placeholder="e.g. Computer Science"
                  className="bg-slate-900/60 border-slate-700/60 text-white"
                  disabled={registering}
                  {...registerForm.register('class_or_department')}
                />
              </div>

              <Button
                type="submit"
                className="w-full bg-indigo-600 hover:bg-indigo-500 py-2.5 font-bold shadow-lg shadow-indigo-600/15 mt-2"
                disabled={registering}
              >
                {registering ? 'Submitting Registration...' : 'Register'}
              </Button>
            </form>
          )}

          <div className="mt-5 pt-4 border-t border-slate-700/40">
            <div className="text-[10px] text-slate-400 grid grid-cols-2 gap-2.5">
              <div><span className="font-semibold text-slate-200">CAMPUS ADMIN:</span> assisivagamon / assisi123@</div>
              <div><span className="font-semibold text-slate-200">DEMO STUDENT:</span> student1 / student123@</div>
              <div><span className="font-semibold text-slate-200">PENDING ADM:</span> 2026-005 to 2026-010</div>
              <div><span className="font-semibold text-slate-200">PLATFORM ADMIN:</span> admin / admin123</div>
            </div>
            <p className="text-[9px] text-center text-slate-500 mt-3 italic">
              * Student registrations require institutional approval before logging in.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
