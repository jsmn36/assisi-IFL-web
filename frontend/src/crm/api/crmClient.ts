// ============================================================
// CRM API Client
//
// Phase 1: All functions return mock data (VITE_CRM_USE_MOCK=true or unset)
// Phase 2: Set VITE_CRM_USE_MOCK=false — functions call real API endpoints
//
// The function signatures never change between phases.
// Only the implementations inside switch between mock and real.
// ============================================================

import axios from 'axios';
import type {
  CRMGuest,
  CRMStay,
  GuestNote,
  GuestPreference,
  GuestDetailResponse,
  GuestListResponse,
  GuestListFilters,
  NoteCreate,
  PreferencesUpdate,
  SegmentSummary,
  SegmentName,
  EmailCampaign,
  CampaignCreate,
  CampaignStats,
  AnalyticsSummary,
  LTVBucket,
  RetentionPoint,
  SyncStatusRecord,
} from '../types/crm';

import {
  MOCK_GUESTS,
  MOCK_STAYS,
  MOCK_NOTES,
  MOCK_PREFERENCES,
  MOCK_CAMPAIGNS,
  MOCK_SEGMENT_SUMMARIES,
  MOCK_ANALYTICS_SUMMARY,
  MOCK_LTV_BUCKETS,
  MOCK_RETENTION_POINTS,
  MOCK_SYNC_STATUS,
} from '../mock/mockData.ts';

// ------------------------------------------------------------------
// Config
// ------------------------------------------------------------------

const USE_MOCK = import.meta.env.VITE_CRM_USE_MOCK !== 'false';
const CRM_BASE = '/api/v1/crm';

// Strip /api/v1 suffix if present — CRM_BASE prepends it explicitly.
const _crmEnv = (import.meta.env.VITE_API_URL ?? import.meta.env.VITE_API_BASE_URL ?? '').toString();
const _crmBaseURL = _crmEnv.replace(/\/?api\/v1\/?$/, '');

const http = axios.create({
  baseURL: _crmBaseURL,
  headers: { 'Content-Type': 'application/json' },
});

// Inject staff name from store into every request
http.interceptors.request.use((config) => {
  try {
    const store = (window as any).__crmStore;
    if (store) {
      config.headers['X-Staff-Name'] = store.getState().currentUser.name;
    }
  } catch {
    // Store not available
  }
  return config;
});

// Simulated latency for mock responses — makes loading states visible in dev
const mockDelay = (ms = 300) => new Promise((r) => setTimeout(r, ms));

// ------------------------------------------------------------------
// Mock helpers
// ------------------------------------------------------------------

function filterAndPaginateGuests(filters: Partial<GuestListFilters>): GuestListResponse {
  const {
    search = '',
    segment = null,
    loyalty_tier = null,
    sort_field = 'last_stay_date',
    sort_dir = 'desc',
    page = 1,
  } = filters;

  const PAGE_SIZE = 25;
  const q = search.toLowerCase();

  let results = [...MOCK_GUESTS];

  // Search
  if (q) {
    results = results.filter(
      (g) =>
        g.full_name.toLowerCase().includes(q) ||
        g.email.toLowerCase().includes(q) ||
        (g.phone?.includes(q) ?? false)
    );
  }

  // Segment filter
  if (segment && segment !== 'all') {
    results = results.filter((g) => g.segments.includes(segment as SegmentName));
  }

  // Loyalty tier filter
  if (loyalty_tier) {
    results = results.filter((g) => g.loyalty_tier === loyalty_tier);
  }

  // Sort
  results.sort((a, b) => {
    let va: number | string = 0;
    let vb: number | string = 0;
    switch (sort_field) {
      case 'name':
        va = a.full_name;
        vb = b.full_name;
        break;
      case 'last_stay_date':
        va = a.last_stay_date ?? '';
        vb = b.last_stay_date ?? '';
        break;
      case 'total_revenue_lifetime':
        va = a.total_revenue_lifetime;
        vb = b.total_revenue_lifetime;
        break;
      case 'total_stays_count':
        va = a.total_stays_count;
        vb = b.total_stays_count;
        break;
    }
    if (va < vb) return sort_dir === 'asc' ? -1 : 1;
    if (va > vb) return sort_dir === 'asc' ? 1 : -1;
    return 0;
  });

  const total = results.length;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const safePage = Math.min(page, pages);
  const items = results.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  return { items, total, page: safePage, page_size: PAGE_SIZE, pages };
}

// In-memory note store for Phase 1 mutations
let mockNotes = [...MOCK_NOTES];
let mockNoteIdCounter = Math.max(...MOCK_NOTES.map((n) => n.note_id)) + 1;

let mockPreferences = [...MOCK_PREFERENCES];

// ------------------------------------------------------------------
// CRM API — Guest endpoints
// ------------------------------------------------------------------

export const crmGuestsApi = {
  list: async (filters: Partial<GuestListFilters> = {}): Promise<GuestListResponse> => {
    if (USE_MOCK) {
      await mockDelay();
      return filterAndPaginateGuests(filters);
    }
    const { data } = await http.get<GuestListResponse>(`${CRM_BASE}/guests`, { params: filters });
    return data;
  },

  get: async (guestId: number): Promise<GuestDetailResponse> => {
    if (USE_MOCK) {
      await mockDelay();
      const guest = MOCK_GUESTS.find((g) => g.guest_id === guestId);
      if (!guest) throw new Error(`Guest ${guestId} not found`);
      const stays = MOCK_STAYS.filter((s) => s.guest_id === guestId);
      const notes = mockNotes.filter((n) => n.guest_id === guestId);
      const preferences = mockPreferences.find((p) => p.guest_id === guestId) ?? null;
      return { guest, stays, notes, preferences };
    }
    const { data } = await http.get<GuestDetailResponse>(`${CRM_BASE}/guests/${guestId}`);
    return data;
  },

  getStays: async (guestId: number): Promise<CRMStay[]> => {
    if (USE_MOCK) {
      await mockDelay(200);
      return MOCK_STAYS.filter((s) => s.guest_id === guestId);
    }
    const { data } = await http.get<CRMStay[]>(`${CRM_BASE}/guests/${guestId}/stays`);
    return data;
  },
};

// ------------------------------------------------------------------
// CRM API — Notes
// ------------------------------------------------------------------

export const crmNotesApi = {
  list: async (guestId: number): Promise<GuestNote[]> => {
    if (USE_MOCK) {
      await mockDelay(150);
      return mockNotes.filter((n) => n.guest_id === guestId);
    }
    const { data } = await http.get<GuestNote[]>(`${CRM_BASE}/guests/${guestId}/notes`);
    return data;
  },

  create: async (guestId: number, payload: NoteCreate): Promise<GuestNote> => {
    if (USE_MOCK) {
      await mockDelay(400);
      const newNote: GuestNote = {
        note_id: mockNoteIdCounter++,
        guest_id: guestId,
        note_type: payload.note_type,
        note_text: payload.note_text,
        visibility: payload.visibility,
        author: 'Maria Rodriguez', // Phase 1: hardcoded
        created_at: new Date().toISOString(),
      };
      mockNotes = [newNote, ...mockNotes];
      return newNote;
    }
    const { data } = await http.post<GuestNote>(`${CRM_BASE}/guests/${guestId}/notes`, payload);
    return data;
  },
};

// ------------------------------------------------------------------
// CRM API — Preferences
// ------------------------------------------------------------------

export const crmPreferencesApi = {
  update: async (guestId: number, payload: PreferencesUpdate): Promise<GuestPreference> => {
    if (USE_MOCK) {
      await mockDelay(400);
      const existing = mockPreferences.find((p) => p.guest_id === guestId);
      const updated: GuestPreference = {
        preference_id: existing?.preference_id ?? guestId + 100,
        guest_id: guestId,
        ...payload,
        updated_at: new Date().toISOString(),
      };
      mockPreferences = mockPreferences.filter((p) => p.guest_id !== guestId);
      mockPreferences.push(updated);
      return updated;
    }
    const { data } = await http.put<GuestPreference>(
      `${CRM_BASE}/guests/${guestId}/preferences`,
      payload
    );
    return data;
  },
};

// ------------------------------------------------------------------
// CRM API — Segments
// ------------------------------------------------------------------

export const crmSegmentsApi = {
  list: async (): Promise<SegmentSummary[]> => {
    if (USE_MOCK) {
      await mockDelay(200);
      return MOCK_SEGMENT_SUMMARIES;
    }
    const { data } = await http.get<SegmentSummary[]>(`${CRM_BASE}/segments`);
    return data;
  },

  getGuests: async (
    segmentName: SegmentName,
    filters: Partial<GuestListFilters> = {}
  ): Promise<GuestListResponse> => {
    if (USE_MOCK) {
      await mockDelay();
      return filterAndPaginateGuests({ ...filters, segment: segmentName });
    }
    const { data } = await http.get<GuestListResponse>(`${CRM_BASE}/segments/${segmentName}/guests`, {
      params: filters,
    });
    return data;
  },
};

// ------------------------------------------------------------------
// CRM API — Campaigns
// ------------------------------------------------------------------

let mockCampaigns = [...MOCK_CAMPAIGNS];
let mockCampaignIdCounter = Math.max(...MOCK_CAMPAIGNS.map((c) => c.campaign_id)) + 1;

export const crmCampaignsApi = {
  list: async (): Promise<EmailCampaign[]> => {
    if (USE_MOCK) {
      await mockDelay(200);
      return [...mockCampaigns];
    }
    const { data } = await http.get<EmailCampaign[]>(`${CRM_BASE}/campaigns`);
    return data;
  },

  create: async (payload: CampaignCreate): Promise<EmailCampaign> => {
    if (USE_MOCK) {
      await mockDelay(500);
      const recipientCount =
        MOCK_SEGMENT_SUMMARIES.find((s) => s.segment_name === payload.segment_name)
          ?.guest_count ?? 0;
      const newCampaign: EmailCampaign = {
        campaign_id: mockCampaignIdCounter++,
        ...payload,
        status: 'draft',
        recipient_count: recipientCount,
        scheduled_at: null,
        sent_at: null,
        created_at: new Date().toISOString(),
      };
      mockCampaigns = [newCampaign, ...mockCampaigns];
      return newCampaign;
    }
    const { data } = await http.post<EmailCampaign>(`${CRM_BASE}/campaigns`, payload);
    return data;
  },

  send: async (campaignId: number): Promise<{ queued: number; skipped: number }> => {
    if (USE_MOCK) {
      await mockDelay(800);
      const campaign = mockCampaigns.find((c) => c.campaign_id === campaignId);
      if (campaign) {
        campaign.status = 'sent';
        campaign.sent_at = new Date().toISOString();
      }
      return { queued: campaign?.recipient_count ?? 0, skipped: 0 };
    }
    const { data } = await http.post<{ queued: number; skipped: number }>(
      `${CRM_BASE}/campaigns/${campaignId}/send`
    );
    return data;
  },

  getStats: async (campaignId: number): Promise<CampaignStats> => {
    if (USE_MOCK) {
      await mockDelay(150);
      const campaign = mockCampaigns.find((c) => c.campaign_id === campaignId);
      const sent = campaign?.recipient_count ?? 0;
      return {
        campaign_id: campaignId,
        recipient_count: sent,
        sent_count: sent,
        delivered_count: Math.round(sent * 0.97),
        opened_count: Math.round(sent * 0.72),
        clicked_count: Math.round(sent * 0.32),
        open_rate: 0.72,
        click_rate: 0.32,
      };
    }
    const { data } = await http.get<CampaignStats>(`${CRM_BASE}/campaigns/${campaignId}/stats`);
    return data;
  },
};

// ------------------------------------------------------------------
// CRM API — Analytics
// ------------------------------------------------------------------

export const crmAnalyticsApi = {
  summary: async (): Promise<AnalyticsSummary> => {
    if (USE_MOCK) {
      await mockDelay(200);
      return MOCK_ANALYTICS_SUMMARY;
    }
    const { data } = await http.get<AnalyticsSummary>(`${CRM_BASE}/analytics/summary`);
    return data;
  },

  ltv: async (): Promise<LTVBucket[]> => {
    if (USE_MOCK) {
      await mockDelay(150);
      return MOCK_LTV_BUCKETS;
    }
    const { data } = await http.get<LTVBucket[]>(`${CRM_BASE}/analytics/ltv`);
    return data;
  },

  retention: async (): Promise<RetentionPoint[]> => {
    if (USE_MOCK) {
      await mockDelay(150);
      return MOCK_RETENTION_POINTS;
    }
    const { data } = await http.get<RetentionPoint[]>(`${CRM_BASE}/analytics/retention`);
    return data;
  },
};

// ------------------------------------------------------------------
// CRM API — Sync status
// ------------------------------------------------------------------

export const crmSyncApi = {
  status: async (): Promise<SyncStatusRecord> => {
    if (USE_MOCK) {
      await mockDelay(100);
      return MOCK_SYNC_STATUS;
    }
    const { data } = await http.get<SyncStatusRecord>(`${CRM_BASE}/sync/status`);
    return data;
  },
};