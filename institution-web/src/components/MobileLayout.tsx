import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Link, useLocation } from 'react-router-dom';
import {
  Menu,
  X,
  Home,
  Calendar,
  Users,
  DoorOpen,
  Briefcase,
  Settings,
  Search,
  Bell,
  User,
  LogOut,
  Shield,
  FileText,
} from 'lucide-react';

/**
 * Mobile Layout Component
 * Responsive layout with mobile drawer for Assisi Social.
 */
export function MobileLayout({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const { user, logout, hasRole } = (useAuth as any)(); // Avoiding strict type errors if context not fully ready
  const location = useLocation();

  // Detect mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close drawer on route change
  useEffect(() => {
    setDrawerOpen(false);
  }, [location.pathname]);

  // Prevent scroll when drawer is open
  useEffect(() => {
    if (drawerOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
  }, [drawerOpen]);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home, roles: ['*'] },
    { name: 'Reservations', href: '/reservations', icon: Calendar, roles: ['*'] },
    { name: 'Guests', href: '/guests', icon: Users, roles: ['*'] },
    { name: 'Rooms', href: '/rooms', icon: DoorOpen, roles: ['*'] },
    { name: 'Search', href: '/search', icon: Search, roles: ['*'] },
    { name: 'Reports', href: '/reports', icon: Briefcase, roles: ['admin', 'manager', 'accountant'] },
    { name: 'User Management', href: '/user-management', icon: Shield, roles: ['admin', 'manager'] },
    { name: 'Audit Logs', href: '/audit-logs', icon: FileText, roles: ['admin', 'manager'] },
    { name: 'Settings', href: '/settings', icon: Settings, roles: ['*'] },
  ];

  const isActive = (path: string) => location.pathname === path;

  const canAccessRoute = (roles: string[]) => {
    if (roles.includes('*')) return true;
    return roles.some(role => hasRole(role));
  };

  if (!isMobile) {
    // Return children without mobile wrapper for desktop
    return <>{children}</>;
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <header className="fixed top-0 left-0 right-0 bg-white border-b z-30 h-16 flex items-center px-4 shadow-sm">
        <div className="flex items-center justify-between w-full">
          <button
            onClick={() => setDrawerOpen(true)}
            className="p-2 -ml-2 rounded-lg hover:bg-gray-100 active:bg-gray-200"
            aria-label="Open menu"
          >
            <Menu className="h-6 w-6" />
          </button>
          
          <h1 className="text-lg font-bold">Assisi Social</h1>
          
          <div className="flex items-center gap-2">
            <button className="p-2 rounded-lg hover:bg-gray-100 active:bg-gray-200 relative">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
            <Link 
              to="/profile" 
              className="p-2 rounded-lg hover:bg-gray-100 active:bg-gray-200"
            >
              <User className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Mobile Drawer */}
      {drawerOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm"
            onClick={() => setDrawerOpen(false)}
          />
          
          {/* Drawer */}
          <div className="fixed inset-y-0 left-0 w-80 max-w-[85vw] bg-white z-50 shadow-xl flex flex-col transform transition-transform duration-300 ease-in-out">
            {/* Drawer Header */}
            <div className="flex items-center justify-between px-4 py-4 border-b">
              <div>
                <h2 className="font-bold text-lg">Assisi Social</h2>
                <p className="text-sm text-gray-600">{user?.username}</p>
              </div>
              <button
                onClick={() => setDrawerOpen(false)}
                className="p-2 rounded-lg hover:bg-gray-100 active:bg-gray-200"
                aria-label="Close menu"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-4">
              {navigation.filter(item => canAccessRoute(item.roles)).map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center gap-3 px-4 py-3 mx-2 rounded-lg transition ${
                      active
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-gray-700 hover:bg-gray-100 active:bg-gray-200'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Drawer Footer */}
            <div className="border-t p-4">
              <button
                onClick={logout}
                className="flex items-center gap-3 w-full px-4 py-3 text-red-600 hover:bg-red-50 active:bg-red-100 rounded-lg transition"
              >
                <LogOut className="h-5 w-5" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </>
      )}

      {/* Main Content */}
      <main className="flex-1 mt-16 pb-20 p-4">
        {children}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-30">
        <div className="flex justify-around items-center h-16">
          {[
            { name: 'Home', href: '/dashboard', icon: Home },
            { name: 'Reservations', href: '/reservations', icon: Calendar },
            { name: 'Search', href: '/search', icon: Search },
            { name: 'More', href: '/settings', icon: Menu },
          ].map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex flex-col items-center justify-center h-full min-w-0 flex-1 ${
                  active ? 'text-blue-600' : 'text-gray-600'
                }`}
              >
                <Icon className="h-6 w-6" />
                <span className="text-[10px] mt-1">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
