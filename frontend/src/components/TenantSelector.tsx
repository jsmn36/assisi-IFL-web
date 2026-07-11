/**
 * TenantSelector
 * Shown after login when the user belongs to more than one tenant.
 * Selecting one calls /auth/select-tenant which returns a tenant-bound
 * token pair; AuthContext promotes the user from "pending" to "logged in".
 */
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Building2, AlertCircle } from 'lucide-react';

export function TenantSelector() {
  const { pendingMemberships, selectTenant } = useAuth();
  const [submittingId, setSubmittingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSelect = async (tenantId: number) => {
    setError(null);
    setSubmittingId(tenantId);
    try {
      await selectTenant(tenantId);
    } catch (err) {
      const message =
        (err as { error?: string; detail?: string; message?: string } | null)?.error ??
        (err as { detail?: string } | null)?.detail ??
        (err as Error | null)?.message ??
        'Failed to select tenant';
      setError(message);
    } finally {
      setSubmittingId(null);
    }
  };

  if (pendingMemberships.length === 0) return null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Choose a workspace</CardTitle>
          <p className="text-sm text-gray-500">
            Your account has access to multiple tenants. Pick one to continue.
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              {error}
            </div>
          )}
          {pendingMemberships.map((m) => (
            <Button
              key={m.tenant_id}
              variant="outline"
              className="w-full justify-between h-auto py-3"
              disabled={submittingId !== null}
              onClick={() => onSelect(m.tenant_id)}
            >
              <span className="flex items-center gap-3">
                <Building2 className="h-5 w-5 text-gray-500" />
                <span className="text-left">
                  <div className="font-medium">{m.tenant_name || m.tenant_slug}</div>
                  <div className="text-xs text-gray-500 capitalize">role: {m.role}</div>
                </span>
              </span>
              {submittingId === m.tenant_id ? (
                <span className="text-xs text-gray-500">Loading…</span>
              ) : m.is_default ? (
                <span className="text-xs text-blue-600">default</span>
              ) : null}
            </Button>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
