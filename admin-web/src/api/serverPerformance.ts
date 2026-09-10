import client from '@/lib/axiosClient';

const BASE = '/api/v1/pos/analytics';

export interface ServerRow {
  server_name: string;
  orders: number;
  covers: number;
  voided_orders: number;
  revenue: number;
  avg_order_value: number;
  upsell_rate: number;
  tip_pct: number;
  avg_prep_time_min: number;
}

export const getServerPerformance = (sinceDays = 30, departmentId?: number) =>
  client
    .get(`${BASE}/servers`, {
      params: { since_days: sinceDays, department_id: departmentId },
    })
    .then(r => r.data as { since_days: number; rows: ServerRow[] });

export const getServerPerformanceByDay = (
  serverName: string,
  sinceDays = 30,
) =>
  client
    .get(`${BASE}/servers/${encodeURIComponent(serverName)}/by-day`, {
      params: { since_days: sinceDays },
    })
    .then(r => r.data);

export const getDepartmentTotals = (sinceDays = 30) =>
  client
    .get(`${BASE}/departments`, { params: { since_days: sinceDays } })
    .then(r => r.data);
