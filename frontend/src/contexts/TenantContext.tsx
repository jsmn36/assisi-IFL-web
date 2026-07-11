/**
 * Tenant + Property context.
 *
 * The tenant id is the JWT claim (read from AuthContext). Property is
 * the user-facing scope inside that tenant — a chain has many properties,
 * an independent has one. Persisted to localStorage so a hard refresh
 * keeps the chosen property; defaults to the first property returned by
 * the backend on first load.
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
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export interface PropertySummary {
  id: number;
  name: string;
  code?: string | null;
}

export interface TenantContextType {
  tenantId: number | null;
  currentPropertyId: number | null;
  availableProperties: PropertySummary[];
  isLoading: boolean;
  switchProperty: (propertyId: number) => void;
  refreshProperties: () => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

const PROPERTY_KEY = 'current_property_id';

function readStoredPropertyId(): number | null {
  const raw = localStorage.getItem(PROPERTY_KEY);
  if (!raw) return null;
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? n : null;
}

export function TenantProvider({ children }: { children: ReactNode }) {
  const { tenantId, isAuthenticated } = useAuth();
  const [availableProperties, setAvailableProperties] = useState<PropertySummary[]>([]);
  const [currentPropertyId, setCurrentPropertyId] = useState<number | null>(readStoredPropertyId);
  const [isLoading, setIsLoading] = useState(false);

  const refreshProperties = useCallback(async () => {
    if (!isAuthenticated) {
      setAvailableProperties([]);
      return;
    }
    setIsLoading(true);
    try {
      const result = await api.getProperties?.();
      const list: PropertySummary[] = Array.isArray(result)
        ? (result as PropertySummary[])
        : (result as { properties?: PropertySummary[] } | undefined)?.properties ?? [];
      setAvailableProperties(list);

      // If the currently-chosen property is no longer in the list (e.g.
      // user switched tenants), fall back to the first available one.
      const stillValid = list.some((p) => p.id === currentPropertyId);
      if (!stillValid) {
        const fallback = list[0]?.id ?? null;
        setCurrentPropertyId(fallback);
        if (fallback != null) {
          localStorage.setItem(PROPERTY_KEY, String(fallback));
        } else {
          localStorage.removeItem(PROPERTY_KEY);
        }
      }
    } catch {
      // Degrade quietly — pages reading currentPropertyId can fall back to
      // their own default. The 401 interceptor handles auth-related errors.
      setAvailableProperties([]);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, currentPropertyId]);

  useEffect(() => {
    refreshProperties();
    // Re-fetch when tenant changes (e.g. user switched tenants).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, isAuthenticated]);

  const switchProperty = useCallback((propertyId: number) => {
    setCurrentPropertyId(propertyId);
    localStorage.setItem(PROPERTY_KEY, String(propertyId));
  }, []);

  const value = useMemo<TenantContextType>(
    () => ({
      tenantId,
      currentPropertyId,
      availableProperties,
      isLoading,
      switchProperty,
      refreshProperties,
    }),
    [tenantId, currentPropertyId, availableProperties, isLoading, switchProperty, refreshProperties]
  );

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant(): TenantContextType {
  const ctx = useContext(TenantContext);
  if (ctx === undefined) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return ctx;
}
