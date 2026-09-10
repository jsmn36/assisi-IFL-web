/**
 * Tier 3 API clients.
 */
import client from '@/lib/axiosClient';

// ===== Ghost Booking Classifier =====

export const listGhostScores = (params?: any) =>
  client.get('/api/v1/ghost-booking', { params }).then((r: any) => r.data);
export const getGhostScore = (id: number) =>
  client.get(`/api/v1/ghost-booking/${id}`).then((r: any) => r.data);
export const scoreReservation = (
  reservation_id: number,
  ip_country?: string,
  billing_country?: string,
) =>
  client
    .post('/api/v1/ghost-booking/score', {
      reservation_id,
      ip_country,
      billing_country,
    })
    .then((r: any) => r.data);
export const evaluateBookingInline = (payload: any) =>
  client.post('/api/v1/ghost-booking/evaluate', payload).then((r: any) => r.data);
export const overrideGhostDecision = (
  id: number,
  new_decision: string,
  reason: string,
) =>
  client
    .post(`/api/v1/ghost-booking/${id}/override`, { new_decision, reason })
    .then((r: any) => r.data);

// ===== Close Cycles =====

export const listCloseCycles = (status?: string) =>
  client
    .get('/api/v1/accounting/close/cycles', { params: { status } })
    .then((r: any) => r.data);
export const getCloseCycle = (id: number) =>
  client.get(`/api/v1/accounting/close/cycles/${id}`).then((r: any) => r.data);
export const getCloseCycleHealth = (id: number) =>
  client.get(`/api/v1/accounting/close/cycles/${id}/health`).then((r: any) => r.data);
export const createCloseCycle = (data: any) =>
  client.post('/api/v1/accounting/close/cycles', data).then((r: any) => r.data);
export const softCloseCycle = (id: number) =>
  client.post(`/api/v1/accounting/close/cycles/${id}/soft-close`).then((r: any) => r.data);
export const hardCloseCycle = (id: number) =>
  client.post(`/api/v1/accounting/close/cycles/${id}/hard-close`).then((r: any) => r.data);
export const reopenCycle = (id: number, reason: string) =>
  client
    .post(`/api/v1/accounting/close/cycles/${id}/reopen`, { reason })
    .then((r: any) => r.data);
export const addCloseTask = (cycleId: number, data: any) =>
  client
    .post(`/api/v1/accounting/close/cycles/${cycleId}/tasks`, data)
    .then((r: any) => r.data);
export const updateCloseTask = (taskId: number, data: any) =>
  client.patch(`/api/v1/accounting/close/tasks/${taskId}`, data).then((r: any) => r.data);
export const recordCloseException = (cycleId: number, data: any) =>
  client
    .post(`/api/v1/accounting/close/cycles/${cycleId}/exceptions`, data)
    .then((r: any) => r.data);
export const resolveCloseException = (exceptionId: number, data: any) =>
  client
    .post(`/api/v1/accounting/close/exceptions/${exceptionId}/resolve`, data)
    .then((r: any) => r.data);

// ===== Cash Forecast =====

export const runCashForecast = (data: any) =>
  client.post('/api/v1/accounting/cash-forecast/run', data).then((r: any) => r.data);
export const listForecastSnapshots = () =>
  client.get('/api/v1/accounting/cash-forecast/snapshots').then((r: any) => r.data);
export const getForecastSnapshot = (id: number) =>
  client
    .get(`/api/v1/accounting/cash-forecast/snapshots/${id}`)
    .then((r: any) => r.data);
export const arAging = () =>
  client.get('/api/v1/accounting/cash-forecast/aging').then((r: any) => r.data);

// ===== Ledger Drift =====

export const scanLedgerDrift = (sinceDays = 14) =>
  client
    .post('/api/v1/accounting/ledger-drift/scan', null, {
      params: { since_days: sinceDays },
    })
    .then((r: any) => r.data);
export const listLedgerDriftAlerts = (params?: any) =>
  client
    .get('/api/v1/accounting/ledger-drift/alerts', { params })
    .then((r: any) => r.data);
export const resolveDriftAlert = (id: number, data: any) =>
  client
    .post(`/api/v1/accounting/ledger-drift/alerts/${id}/resolve`, data)
    .then((r: any) => r.data);

// ===== Decision Audit Ledger =====

export const listDecisionEntries = (params?: any) =>
  client.get('/api/v1/decision-audit', { params }).then((r: any) => r.data);
export const getDecisionEntry = (id: number) =>
  client.get(`/api/v1/decision-audit/${id}`).then((r: any) => r.data);
export const overrideDecision = (id: number, new_outcome: string, reason: string) =>
  client
    .post(`/api/v1/decision-audit/${id}/override`, { new_outcome, reason })
    .then((r: any) => r.data);
export const attachOutcome = (id: number, data: any) =>
  client.post(`/api/v1/decision-audit/${id}/outcome`, data).then((r: any) => r.data);
export const decisionAccuracy = (sinceDays = 60) =>
  client
    .get('/api/v1/decision-audit/_/accuracy', { params: { since_days: sinceDays } })
    .then((r: any) => r.data);

// ===== Filter Templates =====

export const listFilterTemplates = (params?: any) =>
  client.get('/api/v1/filter-templates', { params }).then((r: any) => r.data);
export const recentFilterTemplates = (limit = 5) =>
  client
    .get('/api/v1/filter-templates/recent', { params: { limit } })
    .then((r: any) => r.data);
export const getFilterTemplate = (id: number) =>
  client.get(`/api/v1/filter-templates/${id}`).then((r: any) => r.data);
export const createFilterTemplate = (data: any) =>
  client.post('/api/v1/filter-templates', data).then((r: any) => r.data);
export const updateFilterTemplate = (id: number, data: any) =>
  client.patch(`/api/v1/filter-templates/${id}`, data).then((r: any) => r.data);
export const deleteFilterTemplate = (id: number) =>
  client.delete(`/api/v1/filter-templates/${id}`);
export const recordFilterTemplateUse = (id: number, entity_view: string) =>
  client
    .post(`/api/v1/filter-templates/${id}/use`, { entity_view })
    .then((r: any) => r.data);
