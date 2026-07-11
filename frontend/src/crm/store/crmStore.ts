import { create } from 'zustand';
import type { GuestListFilters, SegmentName, UserRole } from '../types/crm';

export interface CRMUser {
  name: string;
  role: UserRole;
}

const PHASE_1_USER: CRMUser = {
  name: 'Maria Rodriguez',
  role: 'marketing',
};

interface CRMState {
  currentUser: CRMUser;
  filters: GuestListFilters;
  activeDetailTab: 'stays' | 'notes' | 'preferences';
  addNoteModalOpen: boolean;
  addNoteTargetGuestId: number | null;
  editPreferencesModalOpen: boolean;
  campaignWizardStep: 1 | 2 | 3;
  campaignDraft: {
    segment: SegmentName | 'all' | null;
    name: string;
    subject: string;
    previewText: string;
    body: string;
    fromEmail: string;
    fromName: string;
  };
  setSearch: (query: string) => void;
  setSegmentFilter: (segment: SegmentName | 'all' | null) => void;
  setLoyaltyTierFilter: (tier: GuestListFilters['loyalty_tier']) => void;
  setSortField: (field: GuestListFilters['sort_field']) => void;
  toggleSortDir: () => void;
  setPage: (page: number) => void;
  resetFilters: () => void;
  setActiveDetailTab: (tab: 'stays' | 'notes' | 'preferences') => void;
  openAddNoteModal: (guestId: number) => void;
  closeAddNoteModal: () => void;
  openEditPreferencesModal: () => void;
  closeEditPreferencesModal: () => void;
  setCampaignWizardStep: (step: 1 | 2 | 3) => void;
  updateCampaignDraft: (updates: Partial<CRMState['campaignDraft']>) => void;
  resetCampaignDraft: () => void;
}

const DEFAULT_FILTERS: GuestListFilters = {
  search: '',
  segment: null,
  loyalty_tier: null,
  sort_field: 'last_stay_date',
  sort_dir: 'desc',
  page: 1,
};

const DEFAULT_CAMPAIGN_DRAFT: CRMState['campaignDraft'] = {
  segment: null,
  name: '',
  subject: '',
  previewText: '',
  body: '',
  fromEmail: 'marketing@hotel.com',
  fromName: 'Hotel Marketing Team',
};

export const useCRMStore = create<CRMState>((set) => ({
  currentUser: PHASE_1_USER,
  filters: { ...DEFAULT_FILTERS },
  activeDetailTab: 'stays',
  addNoteModalOpen: false,
  addNoteTargetGuestId: null,
  editPreferencesModalOpen: false,
  campaignWizardStep: 1,
  campaignDraft: { ...DEFAULT_CAMPAIGN_DRAFT },
  setSearch: (query) => set((s) => ({ filters: { ...s.filters, search: query, page: 1 } })),
  setSegmentFilter: (segment) => set((s) => ({ filters: { ...s.filters, segment, page: 1 } })),
  setLoyaltyTierFilter: (loyalty_tier) => set((s) => ({ filters: { ...s.filters, loyalty_tier, page: 1 } })),
  setSortField: (sort_field) => set((s) => ({ filters: { ...s.filters, sort_field, page: 1 } })),
  toggleSortDir: () => set((s) => ({ filters: { ...s.filters, sort_dir: s.filters.sort_dir === 'asc' ? 'desc' : 'asc', page: 1 } })),
  setPage: (page) => set((s) => ({ filters: { ...s.filters, page } })),
  resetFilters: () => set(() => ({ filters: { ...DEFAULT_FILTERS } })),
  setActiveDetailTab: (tab) => set(() => ({ activeDetailTab: tab })),
  openAddNoteModal: (guestId) => set(() => ({ addNoteModalOpen: true, addNoteTargetGuestId: guestId })),
  closeAddNoteModal: () => set(() => ({ addNoteModalOpen: false, addNoteTargetGuestId: null })),
  openEditPreferencesModal: () => set(() => ({ editPreferencesModalOpen: true })),
  closeEditPreferencesModal: () => set(() => ({ editPreferencesModalOpen: false })),
  setCampaignWizardStep: (step) => set(() => ({ campaignWizardStep: step })),
  updateCampaignDraft: (updates) => set((s) => ({ campaignDraft: { ...s.campaignDraft, ...updates } })),
  resetCampaignDraft: () => set(() => ({ campaignDraft: { ...DEFAULT_CAMPAIGN_DRAFT }, campaignWizardStep: 1 })),
}));

// Expose store for axios interceptor — avoids circular import
if (typeof window !== 'undefined') {
  (window as any).__crmStore = useCRMStore;
}
