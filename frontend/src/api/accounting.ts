/**
 * Accounting API client
 */
import client from '@/lib/axiosClient';

const BASE = '/api/v1/accounting';

export const setupAccounting = (force = false) =>
  client.post(`${BASE}/setup`, null, { params: { force } }).then(r => r.data);

export const getAccounts = (account_type?: string) =>
  client.get(`${BASE}/accounts`, { params: { account_type } }).then(r => r.data);

export const createAccount = (data: any) =>
  client.post(`${BASE}/accounts`, data).then(r => r.data);

export const getJournalEntries = (params?: {
  from_date?: string; to_date?: string; source?: string; status?: string; limit?: number;
}) =>
  client.get(`${BASE}/journal-entries`, { params }).then(r => r.data);

export const getJournalEntry = (id: number) =>
  client.get(`${BASE}/journal-entries/${id}`).then(r => r.data);

export const createJournalEntry = (data: any) =>
  client.post(`${BASE}/journal-entries`, data).then(r => r.data);

export const postJournalEntry = (id: number) =>
  client.post(`${BASE}/journal-entries/${id}/post`, {}).then(r => r.data);

export const voidJournalEntry = (id: number, reason: string) =>
  client.post(`${BASE}/journal-entries/${id}/void`, null, { params: { reason } }).then(r => r.data);

export const createNightAuditEntry = (data: any) =>
  client.post(`${BASE}/night-audit-entry`, data).then(r => r.data);

export const getPeriods = () =>
  client.get(`${BASE}/periods`).then(r => r.data);

export const closePeriod = (year: number, month: number) =>
  client.post(`${BASE}/periods/close`, { year, month }).then(r => r.data);

export const getProfitAndLoss = (from_date: string, to_date: string) =>
  client.get(`${BASE}/reports/profit-and-loss`, { params: { from_date, to_date } }).then(r => r.data);

export const getBalanceSheet = (as_of: string) =>
  client.get(`${BASE}/reports/balance-sheet`, { params: { as_of } }).then(r => r.data);

export const getNightAuditSummary = (from_date: string, to_date: string) =>
  client.get(`${BASE}/reports/night-audit-summary`, { params: { from_date, to_date } }).then(r => r.data);
