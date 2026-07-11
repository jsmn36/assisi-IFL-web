/**
 * Authentication Context
 *
 * Owns: login/logout, token storage, role + permission checks. After
 * Phase 2 the access token also carries a tenant_id claim and the login
 * response can require tenant selection — that branch is exposed via
 * `pendingMemberships` and resolved by calling `selectTenant(id)`.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import api, { type LoginApiResponse, type TenantMembership } from '@/lib/api';

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  role: string;
  first_name?: string | null;
  last_name?: string | null;
  permissions?: string[];
}

export interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  /** Memberships pending tenant selection. Empty when login completed in one step. */
  pendingMemberships: TenantMembership[];
  /** Active tenant id (mirrors the JWT claim). null when not yet selected. */
  tenantId: number | null;

  login: (username: string, password: string) => Promise<LoginApiResponse>;
  selectTenant: (tenantId: number) => Promise<void>;
  logout: () => void;

  hasRole: (...roles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ACCESS_KEY = 'accessToken';
const ACCESS_KEY_LEGACY = 'auth_token';
const REFRESH_KEY = 'refreshToken';
const USER_KEY = 'user';
const TENANT_KEY = 'tenant_id';

function readJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const segment = token.split('.')[1];
    if (!segment) return null;
    return JSON.parse(atob(segment)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function isTokenExpired(token: string): boolean {
  const payload = readJwtPayload(token);
  const exp = payload?.exp;
  if (typeof exp !== 'number') return true;
  return exp * 1000 < Date.now();
}

function tenantIdFromToken(token: string): number | null {
  const payload = readJwtPayload(token);
  const claim = payload?.tenant_id;
  if (typeof claim === 'number') return claim;
  if (typeof claim === 'string' && /^\d+$/.test(claim)) return Number(claim);
  return null;
}

function persistTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(ACCESS_KEY_LEGACY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

function persistUser(user: AuthUser, tenantId: number | null): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  if (tenantId != null) localStorage.setItem(TENANT_KEY, String(tenantId));
}

function clearSession(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(ACCESS_KEY_LEGACY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(TENANT_KEY);
}

const ROLE_PERMISSIONS: Record<string, string[]> = {
  MANAGER: ['*'],
  RECEPTIONIST: [
    'view_dashboard', 'view_reservations', 'create_reservation',
    'check_in', 'check_out', 'view_guests', 'view_rooms', 'view_housekeeping',
  ],
  CHEF: ['view_dashboard', 'view_pos', 'view_kds', 'view_inventory'],
  WAITER: ['view_dashboard', 'view_pos', 'create_order', 'view_room_service'],
  'INVENTORY STAFF': ['view_dashboard', 'view_inventory', 'adjust_inventory'],
  ACCOUNTANT: ['view_dashboard', 'view_reports', 'view_analytics', 'view_accounting', 'view_audit_logs'],
  'SALES STAFF': ['view_dashboard', 'view_crm', 'view_analytics', 'view_reservations'],
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [tenantId, setTenantId] = useState<number | null>(null);
  const [pendingMemberships, setPendingMemberships] = useState<TenantMembership[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem(USER_KEY);
    const accessToken = localStorage.getItem(ACCESS_KEY);

    if (storedUser && accessToken) {
      if (isTokenExpired(accessToken)) {
        clearSession();
      } else {
        try {
          setUser(JSON.parse(storedUser) as AuthUser);
          setTenantId(tenantIdFromToken(accessToken));
          // Verify session in the background; the 401 interceptor handles
          // refresh, so a network/server error here is non-fatal.
          api.getMe().catch((err: unknown) => {
            const status =
              (err as { status?: number; response?: { status?: number } } | null)?.status ??
              (err as { response?: { status?: number } } | null)?.response?.status;
            if (status === 401 || status === 403) {
              clearSession();
              setUser(null);
              setTenantId(null);
            }
          });
        } catch {
          clearSession();
        }
      }
    }

    setIsLoading(false);
  }, []);

  const login = useCallback(
    async (username: string, password: string): Promise<LoginApiResponse> => {
      const response = await api.login(username, password);
      const { access_token, refresh_token, user: userData, memberships, requires_tenant_selection } = response;

      if (requires_tenant_selection || !access_token || !refresh_token) {
        // Multi-tenant fork: stash memberships, do not finalize the session.
        setPendingMemberships(memberships);
        return response;
      }

      persistTokens(access_token, refresh_token);
      persistUser(userData as AuthUser, tenantIdFromToken(access_token));
      setUser(userData as AuthUser);
      setTenantId(tenantIdFromToken(access_token));
      setPendingMemberships([]);
      return response;
    },
    []
  );

  const selectTenant = useCallback(async (chosenTenantId: number): Promise<void> => {
    const res = await api.selectTenant(chosenTenantId);
    persistTokens(res.access_token, res.refresh_token);

    // /auth/me reflects role for the now-bound tenant
    const me = await api.getMe();
    persistUser(me as AuthUser, res.tenant_id);
    setUser(me as AuthUser);
    setTenantId(res.tenant_id);
    setPendingMemberships([]);
  }, []);

  const logout = useCallback(() => {
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    if (refreshToken) {
      // Best-effort revocation; ignore failures.
      api.logout(refreshToken).catch(() => undefined);
    }
    clearSession();
    setUser(null);
    setTenantId(null);
    setPendingMemberships([]);
  }, []);

  const hasRole = useCallback(
    (...roles: string[]): boolean => {
      if (!user) return false;
      const upperUser = user.role.toUpperCase();
      return roles.map((r) => r.toUpperCase()).includes(upperUser);
    },
    [user]
  );

  const hasPermission = useCallback(
    (permission: string): boolean => {
      if (!user) return false;
      const role = user.role.toUpperCase();
      if (role === 'ADMIN') return true;
      if (user.permissions?.includes(permission)) return true;
      const perms = ROLE_PERMISSIONS[role] ?? [];
      return perms.includes('*') || perms.includes(permission);
    },
    [user]
  );

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      pendingMemberships,
      tenantId,
      login,
      selectTenant,
      logout,
      hasRole,
      hasPermission,
    }),
    [user, isLoading, pendingMemberships, tenantId, login, selectTenant, logout, hasRole, hasPermission]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
