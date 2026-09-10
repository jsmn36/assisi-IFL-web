/**
 * Audit Finding Tracker API client.
 */
import client from '@/lib/axiosClient';

const BASE = '/api/v1/audit-findings';

export type FindingSeverity = 'low' | 'medium' | 'high' | 'critical';
export type FindingStatus =
  | 'open'
  | 'in_remediation'
  | 'awaiting_verification'
  | 'closed'
  | 'overdue'
  | 'escalated';
export type FindingSource =
  | 'internal_audit'
  | 'external_audit'
  | 'regulator'
  | 'self_reported'
  | 'pen_test'
  | 'incident';

export interface AuditFinding {
  id: number;
  reference: string | null;
  title: string;
  description: string | null;
  source: FindingSource;
  severity: FindingSeverity;
  status: FindingStatus;
  owner_user_id: number | null;
  due_date: string | null;
  escalated_at: string | null;
  escalated_to_user_id: number | null;
  closed_at: string | null;
  closed_by: number | null;
  resolution_summary: string | null;
  evidence_url: string | null;
  created_at: string;
  activity?: Array<{
    id: number;
    actor_user_id: number | null;
    event_type: string;
    payload: any;
    created_at: string;
  }>;
}

export const listFindings = (params?: any) =>
  client.get(BASE, { params }).then(r => r.data);

export const getFinding = (id: number) =>
  client.get(`${BASE}/${id}`).then(r => r.data as AuditFinding);

export const createFinding = (data: any) =>
  client.post(BASE, data).then(r => r.data);

export const changeStatus = (id: number, status: FindingStatus, note?: string) =>
  client.post(`${BASE}/${id}/status`, { status, note }).then(r => r.data);

export const addNote = (id: number, note: string) =>
  client.post(`${BASE}/${id}/notes`, { note }).then(r => r.data);

export const assignFinding = (id: number, owner_user_id: number | null) =>
  client.post(`${BASE}/${id}/assign`, { owner_user_id }).then(r => r.data);

export const closeFinding = (
  id: number,
  resolution_summary: string,
  evidence_url?: string,
) =>
  client
    .post(`${BASE}/${id}/close`, { resolution_summary, evidence_url })
    .then(r => r.data);

export const escalateFinding = (id: number, escalated_to_user_id: number) =>
  client
    .post(`${BASE}/${id}/escalate`, { escalated_to_user_id })
    .then(r => r.data);

export const sweepOverdue = () =>
  client.post(`${BASE}/sweep-overdue`).then(r => r.data);
