/**
 * Suppression list API client.
 */
import client from '@/lib/axiosClient';

const BASE = '/api/v1/suppressions';

export type SuppressionChannel = 'email' | 'sms' | 'all';
export type SuppressionReason =
  | 'unsubscribe'
  | 'bounce'
  | 'complaint'
  | 'manual'
  | 'gdpr_erasure'
  | 'invalid';

export interface Suppression {
  id: number;
  address: string;
  channel: SuppressionChannel;
  reason: SuppressionReason;
  notes: string | null;
  source: string | null;
  created_at: string;
  created_by: number | null;
}

export const listSuppressions = (params?: {
  channel?: SuppressionChannel;
  reason?: SuppressionReason;
  search?: string;
  limit?: number;
  offset?: number;
}) => client.get(BASE, { params }).then(r => r.data);

export const createSuppression = (data: {
  address: string;
  channel?: SuppressionChannel;
  reason?: SuppressionReason;
  notes?: string;
}) => client.post(BASE, data).then(r => r.data);

export const bulkCreateSuppressions = (data: {
  addresses: string[];
  channel?: SuppressionChannel;
  reason?: SuppressionReason;
}) => client.post(`${BASE}/bulk`, data).then(r => r.data);

export const deleteSuppression = (id: number) =>
  client.delete(`${BASE}/${id}`);

export const checkSuppression = (
  address: string,
  channel: SuppressionChannel = 'email',
) =>
  client
    .get(`${BASE}/check`, { params: { address, channel } })
    .then(r => r.data);
