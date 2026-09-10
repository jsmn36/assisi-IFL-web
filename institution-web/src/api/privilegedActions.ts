import client from '@/lib/axiosClient';

const BASE = '/api/v1/audit/privileged';

export const getPrivilegedSummary = (sinceDays = 30) =>
  client.get(`${BASE}/summary`, { params: { since_days: sinceDays } }).then(r => r.data);

export const getPrivilegedHeatmap = (
  sinceDays = 30,
  onlyPrivileged = true,
  topN = 20,
) =>
  client
    .get(`${BASE}/heatmap`, {
      params: { since_days: sinceDays, only_privileged: onlyPrivileged, top_n_users: topN },
    })
    .then(r => r.data);

export const getPrivilegedByDOW = (sinceDays = 30) =>
  client
    .get(`${BASE}/day-of-week`, { params: { since_days: sinceDays } })
    .then(r => r.data.buckets as Array<{ day: string; hits: number }>);

export const getTopPrivilegedActions = (sinceDays = 30, limit = 20) =>
  client
    .get(`${BASE}/top-actions`, { params: { since_days: sinceDays, limit } })
    .then(r => r.data.actions as Array<{ action: string; hits: number }>);
