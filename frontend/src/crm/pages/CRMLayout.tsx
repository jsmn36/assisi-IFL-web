import { Outlet, NavLink } from 'react-router-dom';
import { usePermissions } from '../hooks/usePermissions';
import { useCRMStore } from '../store/crmStore';
import { SyncStatus } from '../components/shared/SyncStatus';

export default function CRMLayout() {
  const { can } = usePermissions();
  const { currentUser } = useCRMStore();

  const NAV_ITEMS = [
    { to: '/crm',            label: 'Analytics', icon: '📊', end: true,  show: can('view_analytics') },
    { to: '/crm/guests',     label: 'Guests',    icon: '👥', end: false, show: can('view_guests') },
    { to: '/crm/segments',   label: 'Segments',  icon: '🏷️', end: false, show: can('view_segments') },
    { to: '/crm/campaigns',  label: 'Campaigns', icon: '✉️', end: false, show: can('manage_campaigns') },
  ].filter(i => i.show);

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, sans-serif', background: '#f5f5f3' }}>

      {/* ── Sidebar ── */}
      <nav style={{
        width: 220, minWidth: 220, background: '#0F2040', color: '#fff',
        display: 'flex', flexDirection: 'column', flexShrink: 0,
        boxShadow: '2px 0 8px rgba(0,0,0,0.15)',
      }}>
        {/* Logo */}
        <div style={{ padding: '20px 20px 18px', borderBottom: '1px solid #1e3a5f' }}>
          <div style={{ fontWeight: 700, fontSize: 15, letterSpacing: '0.02em' }}>Guest CRM</div>
          <div style={{ fontSize: 11, color: '#4a7a9b', marginTop: 2 }}>PMS Hotel</div>
        </div>

        {/* Nav links */}
        <div style={{ flex: 1, padding: '8px 0' }}>
          {NAV_ITEMS.map(({ to, label, icon, end }) => (
            <NavLink
              key={to} to={to} end={end}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '11px 20px', textDecoration: 'none', fontSize: 14,
                color: isActive ? '#F59E0B' : '#a0b4cc',
                background: isActive ? 'rgba(245,158,11,0.1)' : 'transparent',
                fontWeight: isActive ? 600 : 400,
                borderLeft: isActive ? '3px solid #F59E0B' : '3px solid transparent',
                transition: 'all 0.1s',
              })}
            >
              <span style={{ fontSize: 15 }}>{icon}</span>
              {label}
            </NavLink>
          ))}
        </div>

        {/* App Switcher */}
        <div style={{ padding: '14px 20px', borderTop: '1px solid #1e3a5f' }}>
          <NavLink to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', textDecoration: 'none', fontSize: 13, color: '#a0b4cc', transition: 'color 0.1s' }} onMouseEnter={(e) => e.currentTarget.style.color = '#fff'} onMouseLeave={(e) => e.currentTarget.style.color = '#a0b4cc'}>
            <span style={{ fontSize: 14 }}>🏨</span> Back to PMS
          </NavLink>
          <NavLink to="/pos" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', textDecoration: 'none', fontSize: 13, color: '#a0b4cc', transition: 'color 0.1s' }} onMouseEnter={(e) => e.currentTarget.style.color = '#fff'} onMouseLeave={(e) => e.currentTarget.style.color = '#a0b4cc'}>
            <span style={{ fontSize: 14 }}>🛒</span> Back to POS
          </NavLink>
        </div>

        {/* User footer */}
        <div style={{ padding: '14px 20px', borderTop: '1px solid #1e3a5f', fontSize: 12, color: '#4a7a9b' }}>
          <div style={{ fontWeight: 500, color: '#a0b4cc' }}>{currentUser.name}</div>
          <div style={{ textTransform: 'capitalize', marginTop: 2 }}>
            {currentUser.role.replace('_', ' ')}
          </div>
        </div>
      </nav>

      {/* ── Main ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Top bar */}
        <div style={{
          height: 52, background: '#fff', borderBottom: '1px solid #e5e7eb',
          display: 'flex', alignItems: 'center', padding: '0 24px',
          justifyContent: 'space-between', flexShrink: 0,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}>
          <span style={{ fontSize: 13, color: '#9ca3af' }}>
            Guest Relationship Management
          </span>
          {/* SyncStatus component added in Week 11 Day 4 */}
          {can('view_sync_status') && <SyncStatus />}
        </div>

        {/* Page outlet */}
        <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}