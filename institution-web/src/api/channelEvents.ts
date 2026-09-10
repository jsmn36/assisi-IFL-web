/**
 * Channel Manager webhook event audit + replay API client.
 */
import client from '@/lib/axiosClient';

const BASE = '/cm/admin/events';

export interface ChannelEvent {
  event_id: string;
  property_id: string;
  channel: string;
  external_reference: string | null;
  status: string;
  retry_count: number;
  checksum: string;
  idempotency_key: string | null;
  received_at: string;
  pms_verdict: Record<string, unknown> | null;
  raw_payload?: Record<string, unknown> | null;
}

export interface DLQGroup {
  error_code: string;
  count: number;
  last_seen: string;
  channels: string[];
}

export interface ReplayResult {
  original_event_id: string;
  replayed_event_id: string | null;
  status: string;
  message: string;
}

export const listChannelEvents = (params?: {
  channel?: string;
  status?: string;
  since_hours?: number;
  external_reference?: string;
  limit?: number;
  offset?: number;
}) => client.get(BASE, { params }).then(r => r.data);

export const getChannelEvent = (eventId: string) =>
  client.get(`${BASE}/${eventId}`).then(r => r.data as ChannelEvent);

export const getChannelEventProcessing = (eventId: string) =>
  client.get(`${BASE}/${eventId}/processing`).then(r => r.data);

export const getChannelEventDLQ = (sinceHours = 168) =>
  client.get(`${BASE}/dlq`, { params: { since_hours: sinceHours } }).then(r => r.data);

export const replayChannelEvent = (eventId: string, apiKey?: string) =>
  client
    .post(`${BASE}/${eventId}/replay`, { api_key: apiKey, bump_retry_count: true })
    .then(r => r.data as ReplayResult);

export const replayChannelEventsBulk = (eventIds: string[], apiKey?: string) =>
  client
    .post(`${BASE}/replay-bulk`, { event_ids: eventIds, api_key: apiKey })
    .then(r => r.data);
