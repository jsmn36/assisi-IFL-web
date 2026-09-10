/**
 * Main Layout Component
 */
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useState } from 'react';
import {
  Home,
  Calendar,
  Users,
  DoorOpen,
  DoorClosed,
  Bed,
  BarChart3,
  Cog,
  Bell,
  DollarSign,
  Sparkles,
  TrendingUp,
  Settings,
  LogOut,
  UserCog,
  Shield,
  FileText,
  Search,
  ShoppingCart,
  BookOpen,
  Package,
  Contact,
  Monitor,
  Zap,
  Inbox,
  AlertOctagon,
  Flame,
  CalendarCheck,
  ClipboardList,
  KeyRound,
  Banknote,
  AlertTriangle,
  Ghost,
  Lock,
  Wallet,
  ScrollText,
  Menu as MenuIcon,
  X,
} from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { user, logout, hasRole, hasPermission } = useAuth();
  const { compactSidebar } = useTheme();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isQuickNavOpen, setIsQuickNavOpen] = useState(false);
  const location = useLocation();
  const isAdmin = hasRole('admin', 'manager');

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home, permission: 'view_dashboard' },
    { name: 'Reservations', href: '/reservations', icon: Calendar, permission: 'view_reservations' },
    { name: 'Check-in', href: '/check-in', icon: DoorOpen, permission: 'check_in' },
    { name: 'Check-out', href: '/check-out', icon: DoorClosed, permission: 'check_out' },
    { name: 'Guests', href: '/guests', icon: Users, permission: 'view_guests' },
    { name: 'Rooms', href: '/rooms', icon: Bed, permission: 'view_rooms' },
    { name: 'Housekeeping', href: '/housekeeping', icon: Sparkles, permission: 'view_housekeeping' },
    { name: 'Rates', href: '/rates', icon: DollarSign, permission: 'view_rates' },
    { name: 'Analytics', href: '/analytics', icon: TrendingUp, permission: 'view_analytics' },
    { name: 'Reports', href: '/reports', icon: BarChart3, permission: 'view_reports' },
    { name: 'Operations', href: '/operations', icon: Cog, permission: 'view_operations' },
    { name: 'Notifications', href: '/notifications', icon: Bell, permission: 'view_notifications' },
    { name: 'Users', href: '/user-management', icon: UserCog, permission: 'view_users' },
    { name: 'Settings', href: '/settings', icon: Settings, permission: 'view_settings' },
    { name: 'Compliance', href: '/compliance', icon: Shield, permission: 'view_compliance' },
    { name: 'Audit Logs', href: '/audit-logs', icon: FileText, permission: 'view_audit_logs' },
    { name: 'Channel Events', href: '/channel-events', icon: Inbox, permission: 'view_audit_logs' },
    { name: 'Search Analytics', href: '/search-analytics', icon: Search, permission: 'view_audit_logs' },
    { name: 'Suppressions', href: '/suppressions', icon: AlertOctagon, permission: 'view_audit_logs' },
    { name: 'Compliance Calendar', href: '/compliance-calendar', icon: CalendarCheck, permission: 'view_compliance' },
    { name: 'Audit Findings', href: '/audit-findings', icon: ClipboardList, permission: 'view_compliance' },
    { name: 'Privileged Actions', href: '/privileged-actions', icon: Flame, permission: 'view_audit_logs' },
    { name: 'Server Performance', href: '/server-performance', icon: TrendingUp, permission: 'view_pos' },
    { name: 'Anomalies', href: '/anomalies', icon: AlertTriangle, permission: 'view_analytics' },
    { name: 'Guest LTV', href: '/guest-ltv', icon: TrendingUp, permission: 'view_analytics' },
    { name: 'Reconciliation', href: '/reconciliation', icon: Banknote, permission: 'view_accounting' },
    { name: 'JIT Access', href: '/jit-access', icon: KeyRound, permission: 'view_users' },
    { name: 'Ghost Booking', href: '/ghost-booking', icon: Ghost, permission: 'view_reservations' },
    { name: 'Continuous Close', href: '/continuous-close', icon: Lock, permission: 'view_accounting' },
    { name: 'Cash Forecast', href: '/cash-forecast', icon: Wallet, permission: 'view_accounting' },
    { name: 'Decision Audit', href: '/decision-audit', icon: ScrollText, permission: 'view_audit_logs' },
    { name: 'Search', href: '/search', icon: Search, permission: 'view_search' },
    { name: 'CRM', href: '/crm', icon: Contact, permission: 'view_crm' },
    { name: 'POS', href: '/pos', icon: ShoppingCart, permission: 'view_pos' },
    { name: 'Accounting', href: '/accounting', icon: BookOpen, permission: 'view_accounting' },
    { name: 'Inventory', href: '/inventory', icon: Package, permission: 'view_inventory' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-[hsl(222,47%,8%)] overflow-hidden relative">
      {/* Sidebar - Desktop */}
      <div className={`
        fixed inset-y-0 left-0 z-50 bg-gray-900 flex flex-col transition-all duration-300 md:translate-x-0
        ${compactSidebar ? 'w-16' : 'w-64'}
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Mobile close button */}
        <button 
          onClick={() => setIsSidebarOpen(false)}
          className="md:hidden absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X className="h-6 w-6" />
        </button>

        {/* Logo */}
        <div className={`flex h-16 items-center border-b border-gray-800 ${compactSidebar ? 'justify-center px-2' : 'px-6'}`}>
          {compactSidebar ? (
            <span className="text-white font-bold text-lg">A</span>
          ) : (
            <h1 className="text-xl font-bold text-white">Assisi Social</h1>
          )}
        </div>

        {/* Navigation */}
        <nav className="mt-6 px-2 overflow-y-auto flex-1 scrollbar-thin">
          {navigation.filter(item => !item.permission || hasPermission(item.permission)).map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => setIsSidebarOpen(false)}
                title={compactSidebar ? item.name : undefined}
                className={`flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors mb-0.5 ${
                  compactSidebar ? 'justify-center gap-0' : 'gap-3'
                } ${
                  isActive(item.href)
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {!compactSidebar && item.name}
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="border-t border-gray-800 p-3">
          {compactSidebar ? (
            <div className="flex flex-col items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-gray-700 flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {user?.username.charAt(0).toUpperCase()}
                </span>
              </div>
              <button onClick={logout} className="text-gray-400 hover:text-white transition-colors">
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-gray-700 flex items-center justify-center">
                  <span className="text-sm font-medium text-white">
                    {user?.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="text-sm">
                  <p className="font-medium text-white">{user?.username}</p>
                  <p className="text-gray-400">{user?.role}</p>
                </div>
              </div>
              <button onClick={logout} className="text-gray-400 hover:text-white transition-colors">
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${compactSidebar ? 'md:pl-16' : 'md:pl-64'}`}>
        {/* Header */}
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-white dark:bg-[hsl(220,40%,12%)] dark:border-[hsl(218,28%,20%)] px-4 md:px-6">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(true)}
              className="md:hidden p-2 -ml-2 text-gray-500 hover:bg-gray-100 rounded-lg"
            >
              <MenuIcon className="h-6 w-6" />
            </button>
            <h2 className="text-lg md:text-xl font-bold text-gray-900 dark:text-gray-100 truncate">
              {navigation.find((item) => isActive(item.href))?.name || 'Assisi Social'}
            </h2>
          </div>
          <div className="text-sm text-gray-500">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </div>
        </header>

        {/* Page content */}
        <main className="p-6 overflow-auto flex-1 relative scrollbar-thin dark:bg-[hsl(222,47%,8%)]">{children}</main>
        
        {/* Quick Nav for Roles with Terminal Access */}
        {(isAdmin || hasPermission('view_pos') || hasPermission('view_kds') || hasPermission('view_inventory') || hasPermission('view_crm')) && (
          <div className="fixed bottom-6 right-6 flex flex-col gap-3 items-end z-50">
            <div className={`flex flex-col gap-3 transition-all duration-300 transform ${
              isQuickNavOpen 
              ? 'opacity-100 translate-y-0 pointer-events-auto' 
              : 'opacity-0 translate-y-4 pointer-events-none'
            }`}>
               {(isAdmin || hasPermission('view_pos')) && (
                 <Link 
                   to="/pos/terminal" 
                   onClick={() => setIsQuickNavOpen(false)}
                   className="bg-amber-600 text-white p-3 rounded-full shadow-lg hover:bg-amber-700 flex items-center gap-2" 
                   title="POS Terminal"
                 >
                  <ShoppingCart className="h-5 w-5" />
                  <span className="text-xs font-bold whitespace-nowrap pr-2">Terminal</span>
                 </Link>
               )}
               {(isAdmin || hasPermission('view_kds')) && (
                 <Link 
                   to="/pos/kds" 
                   onClick={() => setIsQuickNavOpen(false)}
                   className="bg-red-600 text-white p-3 rounded-full shadow-lg hover:bg-red-700 flex items-center gap-2" 
                   title="KDS"
                 >
                  <Monitor className="h-5 w-5" />
                  <span className="text-xs font-bold whitespace-nowrap pr-2">Kitchen</span>
                 </Link>
               )}
               {(isAdmin || hasPermission('view_crm')) && (
                 <Link 
                   to="/crm" 
                   onClick={() => setIsQuickNavOpen(false)}
                   className="bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 flex items-center gap-2" 
                   title="CRM"
                 >
                  <Contact className="h-5 w-5" />
                  <span className="text-xs font-bold whitespace-nowrap pr-2">CRM</span>
                 </Link>
               )}
               {(isAdmin || hasPermission('view_inventory')) && (
                 <Link 
                   to="/inventory/terminal" 
                   onClick={() => setIsQuickNavOpen(false)}
                   className="bg-emerald-600 text-white p-3 rounded-full shadow-lg hover:bg-emerald-700 flex items-center gap-2" 
                   title="Stock Terminal"
                 >
                  <Package className="h-5 w-5" />
                  <span className="text-xs font-bold whitespace-nowrap pr-2">Stock</span>
                 </Link>
               )}
            </div>
            <button 
              onClick={() => setIsQuickNavOpen(!isQuickNavOpen)}
              className={`p-4 rounded-full shadow-2xl transition-all active:scale-90 ${
                isQuickNavOpen ? 'bg-amber-500 text-white rotate-45' : 'bg-gray-900 text-amber-500'
              }`}
            >
              <Zap className="h-6 w-6" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
