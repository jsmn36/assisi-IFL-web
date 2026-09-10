/**
 * Tier 2 API clients — all in one module to keep the new surface area easy
 * to navigate. Each section maps to one backend feature.
 */
import client from '@/lib/axiosClient';

// ===== Anomaly Alerts =====

export const listAnomalies = (params?: any) =>
  client.get('/api/v1/anomalies', { params }).then(r => r.data);
export const runAnomalyScan = () =>
  client.post('/api/v1/anomalies/scan').then(r => r.data);
export const recomputeBaseline = (metric_key: string, scope = 'all') =>
  client
    .post('/api/v1/anomalies/recompute-baseline', null, {
      params: { metric_key, scope },
    })
    .then(r => r.data);
export const acknowledgeAnomaly = (id: number, notes?: string) =>
  client.post(`/api/v1/anomalies/${id}/acknowledge`, { notes }).then(r => r.data);
export const setAnomalyStatus = (id: number, status: string) =>
  client.post(`/api/v1/anomalies/${id}/status`, { status }).then(r => r.data);
export const muteAnomaly = (data: any) =>
  client.post('/api/v1/anomalies/mutes', data).then(r => r.data);
export const listMetrics = () =>
  client.get('/api/v1/anomalies/metrics').then(r => r.data.metrics as string[]);

// ===== Guest LTV =====

export const listGuestLTV = (params?: any) =>
  client.get('/api/v1/guest-ltv', { params }).then(r => r.data);
export const cohortSummary = () =>
  client.get('/api/v1/guest-ltv/cohorts').then(r => r.data);
export const topGuests = (n = 50) =>
  client.get('/api/v1/guest-ltv/top', { params: { n } }).then(r => r.data);
export const exportLTVCsv = (cohort?: string, minStays?: number) =>
  client
    .get('/api/v1/guest-ltv/export.csv', {
      params: { cohort, min_stays: minStays },
      responseType: 'blob',
    })
    .then(r => r.data);

// ===== Reconciliation =====

export const listFeedEntries = (params?: any) =>
  client
    .get('/api/v1/accounting/reconciliation/entries', { params })
    .then(r => r.data);
export const listSuggestions = (entryId: number) =>
  client
    .get(`/api/v1/accounting/reconciliation/entries/${entryId}/suggestions`)
    .then(r => r.data);
export const runReconciliation = () =>
  client.post('/api/v1/accounting/reconciliation/run').then(r => r.data);
export const approveMatch = (id: number) =>
  client
    .post(`/api/v1/accounting/reconciliation/matches/${id}/approve`)
    .then(r => r.data);
export const rejectMatch = (id: number) =>
  client
    .post(`/api/v1/accounting/reconciliation/matches/${id}/reject`)
    .then(r => r.data);
export const ignoreFeedEntry = (id: number) =>
  client
    .post(`/api/v1/accounting/reconciliation/entries/${id}/ignore`)
    .then(r => r.data);
export const importFeedEntries = (entries: any[]) =>
  client
    .post('/api/v1/accounting/reconciliation/import', { entries })
    .then(r => r.data);
export const reconSummary = () =>
  client.get('/api/v1/accounting/reconciliation/summary').then(r => r.data);

// ===== Upsell Chains =====

export const listUpsellChains = () =>
  client.get('/api/v1/upsells/chains').then(r => r.data);
export const createUpsellChain = (data: any) =>
  client.post('/api/v1/upsells/chains', data).then(r => r.data);
export const updateUpsellChain = (id: number, data: any) =>
  client.patch(`/api/v1/upsells/chains/${id}`, data).then(r => r.data);
export const deleteUpsellChain = (id: number) =>
  client.delete(`/api/v1/upsells/chains/${id}`);
export const processDueUpsells = () =>
  client.post('/api/v1/upsells/process-due').then(r => r.data);
export const chainMetrics = (id: number) =>
  client.get(`/api/v1/upsells/chains/${id}/metrics`).then(r => r.data);

// ===== Feedback =====

export const listFeedback = (params?: any) =>
  client.get('/api/v1/feedback', { params }).then(r => r.data);
export const submitFeedback = (data: any) =>
  client.post('/api/v1/feedback', data).then(r => r.data);
export const resolveFeedback = (id: number, summary: string) =>
  client
    .post(`/api/v1/feedback/${id}/resolve`, { resolution_summary: summary })
    .then(r => r.data);
export const updateResolution = (id: number, data: any) =>
  client.patch(`/api/v1/feedback/${id}/resolution`, data).then(r => r.data);

// ===== JIT Access =====

export const listGrants = (params?: any) =>
  client.get('/api/v1/jit-access/grants', { params }).then(r => r.data);
export const issueGrant = (data: any) =>
  client.post('/api/v1/jit-access/grants', data).then(r => r.data);
export const revokeGrant = (id: number, reason?: string) =>
  client.post(`/api/v1/jit-access/grants/${id}/revoke`, { reason }).then(r => r.data);
export const sweepExpiredGrants = () =>
  client.post('/api/v1/jit-access/sweep-expired').then(r => r.data);
export const myActiveGrants = () =>
  client.get('/api/v1/jit-access/me/active').then(r => r.data);

// ===== Corporate =====

export const listCorporate = (params?: any) =>
  client.get('/api/v1/corporate/accounts', { params }).then(r => r.data);
export const createCorporate = (data: any) =>
  client.post('/api/v1/corporate/accounts', data).then(r => r.data);
export const corporateMembers = (id: number) =>
  client.get(`/api/v1/corporate/accounts/${id}/members`).then(r => r.data);
export const addCorporateMember = (id: number, data: any) =>
  client.post(`/api/v1/corporate/accounts/${id}/members`, data).then(r => r.data);
export const corporateSpend = (id: number, sinceDays = 365) =>
  client
    .get(`/api/v1/corporate/accounts/${id}/spend`, {
      params: { since_days: sinceDays },
    })
    .then(r => r.data);

// ===== Cost per dish + Waste =====

export const costPerDish = (categoryId?: number) =>
  client
    .get('/api/v1/pos/analytics/cost-per-dish', { params: { category_id: categoryId } })
    .then(r => r.data);
export const costPerDishByCategory = () =>
  client.get('/api/v1/pos/analytics/cost-per-dish/by-category').then(r => r.data);

export const recordWaste = (data: any) =>
  client.post('/api/v1/pos/waste', data).then(r => r.data);
export const listWaste = (params?: any) =>
  client.get('/api/v1/pos/waste', { params }).then(r => r.data);
export const wasteSummary = (sinceDays = 30) =>
  client
    .get('/api/v1/pos/waste/summary', { params: { since_days: sinceDays } })
    .then(r => r.data);

// ===== DSAR & Consent =====

export const listDSARRequests = (params?: any) =>
  client.get('/api/v1/dsar/requests', { params }).then(r => r.data);
export const intakeDSAR = (data: any) =>
  client.post('/api/v1/dsar/requests', data).then(r => r.data);
export const verifyDSARIdentity = (id: number) =>
  client.post(`/api/v1/dsar/requests/${id}/verify-identity`).then(r => r.data);
export const deliverDSAR = (id: number, data: any) =>
  client.post(`/api/v1/dsar/requests/${id}/deliver`, data).then(r => r.data);

export const listConsentVersions = (kind?: string) =>
  client
    .get('/api/v1/dsar/consent/versions', { params: { kind } })
    .then(r => r.data);
export const publishConsent = (data: any) =>
  client.post('/api/v1/dsar/consent/versions', data).then(r => r.data);

// ===== Supplier scorecard =====

export const vendorScorecard = (sinceDays = 180) =>
  client
    .get('/api/v1/inventory/vendors/scorecard', { params: { since_days: sinceDays } })
    .then(r => r.data);
export const vendorWarnings = (sinceDays = 180) =>
  client
    .get('/api/v1/inventory/vendors/warnings', { params: { since_days: sinceDays } })
    .then(r => r.data);

// ===== Allocation pool =====

export const upsertAllocation = (data: any) =>
  client.post('/api/v1/allocations', data).then(r => r.data);
export const setChannelBuffer = (data: any) =>
  client.post('/api/v1/allocations/channel-buffers', data).then(r => r.data);
export const createHold = (data: any) =>
  client.post('/api/v1/allocations/holds', data).then(r => r.data);
export const releaseHold = (id: number) =>
  client.post(`/api/v1/allocations/holds/${id}/release`).then(r => r.data);
export const allocationSnapshot = (roomTypeId: number, night: string) =>
  client
    .get('/api/v1/allocations/snapshot', {
      params: { room_type_id: roomTypeId, night },
    })
    .then(r => r.data);
export const allocationRange = (roomTypeId: number, start: string, end: string) =>
  client
    .get('/api/v1/allocations/range', {
      params: { room_type_id: roomTypeId, start, end },
    })
    .then(r => r.data);
export const safeToSell = (roomTypeId: number, night: string, channel?: string) =>
  client
    .get('/api/v1/allocations/safe-to-sell', {
      params: { room_type_id: roomTypeId, night, channel },
    })
    .then(r => r.data);
