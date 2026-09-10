import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { 
  Home, 
  Compass, 
  MessageSquare, 
  Users, 
  User as UserIcon, 
  LogOut, 
  Sun, 
  Moon,
  GraduationCap,
  ShieldAlert,
  Building
} from 'lucide-react';

interface StudentLayoutProps {
  children: React.ReactNode;
}

export default function StudentLayout({ children }: StudentLayoutProps) {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    try {
      logout();
    } catch (e) {
      console.error(e);
    }
    localStorage.clear();
    sessionStorage.clear();
    navigate('/login', { replace: true });
  };

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const navItems = [
    { name: 'Home', icon: Home, path: '/student-home' },
    { name: 'Explore', icon: Compass, path: '/explore' },
    { name: 'Messages', icon: MessageSquare, path: '/chat' },
    { name: 'Groups', icon: Users, path: '/classrooms' },
    { 
      name: 'Profile', 
      icon: UserIcon, 
      path: user ? `/students/profile/${user.username}` : '/student-home' 
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex transition-colors duration-200">
      {/* Sidebar - Instagram style */}
      <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between p-6 fixed h-full left-0 z-30">
        <div>
          {/* Logo Header */}
          <div className="flex items-center gap-3 mb-10 px-2">
            <div className="h-10 w-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white">
              <GraduationCap className="h-6 w-6" />
            </div>
            <div>
              <h1 className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-indigo-600 to-indigo-400 dark:from-white dark:to-indigo-300 bg-clip-text text-transparent">
                Assisi Social
              </h1>
              <p className="text-[10px] text-slate-400 dark:text-slate-500 font-semibold uppercase tracking-wider">
                Student Network
              </p>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center gap-4 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-150 ${
                    isActive 
                      ? 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400' 
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  <Icon className={`h-5 w-5 ${isActive ? 'stroke-[2.5px]' : 'stroke-[2px]'}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Quick Cross-Portal Switcher */}
          <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-800 space-y-2">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 dark:text-slate-500 px-2 block">
              System Control
            </span>
            <a
              href="http://localhost:3001"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-bold text-xs bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 transition-all group"
            >
              <ShieldAlert className="h-4.5 w-4.5 text-rose-500 flex-shrink-0" />
              <div className="overflow-hidden">
                <span className="block truncate">Super Admin Center</span>
                <span className="text-[9px] text-slate-500 dark:text-slate-400 font-normal truncate block">Main Admin Panel</span>
              </div>
            </a>
            <a
              href="http://localhost:3002"
              className="flex items-center gap-3 px-3 py-2 rounded-xl font-medium text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-all"
            >
              <Building className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0" />
              <span>Branch Space</span>
            </a>
          </div>
        </div>

        {/* Footer controls & Profile preview */}
        <div className="space-y-4">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="w-full flex items-center gap-4 px-4 py-3 rounded-xl font-medium text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-all"
          >
            {theme === 'dark' ? (
              <>
                <Sun className="h-5 w-5 text-amber-500" />
                <span>Light Mode</span>
              </>
            ) : (
              <>
                <Moon className="h-5 w-5 text-indigo-500" />
                <span>Dark Mode</span>
              </>
            )}
          </button>

          {/* Sign Out */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-4 px-4 py-3 rounded-xl font-medium text-sm text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-all"
          >
            <LogOut className="h-5 w-5" />
            <span>Log Out</span>
          </button>

          {/* User info bubble */}
          {user && (
            <div className="flex items-center gap-3 px-3 py-2 border-t border-slate-200 dark:border-slate-800 pt-4">
              <img
                src={`https://api.dicebear.com/7.x/adventurer/svg?seed=${user.username}`}
                alt="Profile"
                className="h-9 w-9 rounded-full bg-slate-200 dark:bg-slate-700"
              />
              <div className="overflow-hidden">
                <p className="font-semibold text-xs truncate">
                  {user.first_name ? `${user.first_name} ${user.last_name}` : user.username}
                </p>
                <p className="text-[10px] text-slate-400 truncate">
                  @{user.username}
                </p>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 ml-64 min-h-screen">
        {children}
      </main>
    </div>
  );
}
