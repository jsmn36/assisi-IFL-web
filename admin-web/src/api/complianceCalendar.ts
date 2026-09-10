/**
 * Compliance Calendar API client.
 */
import client from '@/lib/axiosClient';

const BASE = '/api/v1/compliance-calendar';

export type ComplianceCategory =
  | 'license'
  | 'filing'
  | 'renewal'
  | 'audit'
  | 'training'
  | 'policy'
  | 'other';

export type ComplianceStatus =
  | 'open'
  | 'in_progress'
  | 'done'
  | 'overdue'
  | 'waived';

export interface ComplianceItem {
  id: number;
  title: string;
  description: string | null;
  category: ComplianceCategory;
  status: ComplianceStatus;
  owner_user_id: number | null;
  due_date: string;
  recurrence_months: number | null;
  reminder_90d_sent_at: string | null;
  reminder_30d_sent_at: string | null;
  reminder_7d_sent_at: string | null;
  completed_at: string | null;
  completed_by: number | null;
  completion_evidence_url: string | null;
  notes: string | null;
  created_at: string;
}

export const listItems = (params?: any) =>
  client.get(BASE, { params }).then(r => r.data);

export const createItem = (data: any) =>
  client.post(BASE, data).then(r => r.data);

export const updateItem = (id: number, data: any) =>
  client.patch(`${BASE}/${id}`, data).then(r => r.data);

export const completeItem = (id: number, evidence_url?: string) =>
  client.post(`${BASE}/${id}/complete`, { evidence_url }).then(r => r.data);

export const deleteItem = (id: number) =>
  client.delete(`${BASE}/${id}`);

export const triggerSweep = () =>
  client.post(`${BASE}/sweep`).then(r => r.data);
