import { useCRMStore } from '../store/crmStore';

type Permission =
  | 'view_guests'
  | 'add_notes'
  | 'view_segments'
  | 'manage_campaigns'
  | 'view_analytics'
  | 'view_sync_status';

const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  front_desk: ['view_guests', 'add_notes', 'view_segments', 'view_sync_status'],
  marketing: ['view_guests', 'add_notes', 'view_segments', 'manage_campaigns', 'view_analytics', 'view_sync_status'],
  manager: ['view_guests', 'view_segments', 'view_analytics', 'view_sync_status'],
  admin: ['view_guests', 'add_notes', 'view_segments', 'manage_campaigns', 'view_analytics', 'view_sync_status'],
};

export function usePermissions() {
  const { currentUser } = useCRMStore();

  function can(permission: Permission): boolean {
    const perms = ROLE_PERMISSIONS[currentUser.role] ?? [];
    return perms.includes(permission);
  }

  return { can, role: currentUser.role, userName: currentUser.name };
}
