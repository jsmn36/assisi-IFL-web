// ============================================================
// CRM Type Definitions
// Single source of truth for all CRM frontend types.
// These mirror the CRM backend Pydantic schemas exactly.
// DO NOT add PMS model types here — those live in src/types/api.ts
// ============================================================

// ------------------------------------------------------------------
// Enums
// ------------------------------------------------------------------

export type LoyaltyTier = 'bronze' | 'silver' | 'gold' | 'platinum';

export type NoteType = 'preference' | 'issue' | 'vip' | 'general' | 'special_request';

export type NoteVisibility = 'internal' | 'guest_visible';

export type SegmentName =
  | 'vip'
  | 'repeat'
  | 'first_time'
  | 'inactive'
  | 'high_spender'
  | 'frequent';

export type CampaignStatus = 'draft' | 'sending' | 'sent' | 'failed';

export type CampaignSendStatus = 'queued' | 'sent' | 'delivered' | 'opened' | 'clicked' | 'failed';

export type SyncStatus = 'success' | 'running' | 'error' | 'never';

export type UserRole = 'front_desk' | 'marketing' | 'manager' | 'admin';

// ------------------------------------------------------------------
// Mirror entities (synced from PMS — read-only in CRM)
// ------------------------------------------------------------------

export interface CRMGuest {
  guest_id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  country: string | null;               // ISO 2-char country code
  loyalty_tier: LoyaltyTier | null;
  registration_date: string | null;     // ISO date string
  total_stays_count: number;
  total_revenue_lifetime: number;       // decimal as number
  last_stay_date: string | null;        // ISO date string
  // Segment flags (computed)
  is_vip: boolean;
  is_repeat: boolean;
  is_inactive: boolean;
  is_high_spender: boolean;
  // Sync metadata
  pms_created_at: string | null;
  pms_updated_at: string | null;
  crm_synced_at: string;
  // Derived / convenience
  full_name: string;
  avg_revenue_per_stay: number;
  segments: SegmentName[];
}

export interface CRMStay {
  stay_id: number;
  guest_id: number;
  reservation_id: number | null;
  room_number: string | null;
  check_in_date: string;                // ISO date string
  check_out_date: string;               // ISO date string
  nights: number;
  status: 'active' | 'checked_out';
  total_revenue: number;
  room_revenue: number;
  other_revenue: number;
  crm_synced_at: string;
}

export interface CRMCharge {
  charge_id: number;
  stay_id: number;
  guest_id: number;
  charge_type: string;
  description: string | null;
  amount: number;
  charge_date: string;                  // ISO date string
  status: string;
  crm_synced_at: string;
}

// ------------------------------------------------------------------
// CRM-only entities (writable by hotel staff)
// ------------------------------------------------------------------

export interface GuestNote {
  note_id: number;
  guest_id: number;
  note_type: NoteType;
  note_text: string;
  visibility: NoteVisibility;
  author: string;
  created_at: string;                   // ISO datetime string
}

export interface GuestPreference {
  preference_id: number;
  guest_id: number;
  room_preference: string | null;
  dietary_restrictions: string | null;
  special_occasions: string | null;
  other_notes: string | null;
  updated_at: string;
}

export interface GuestSegment {
  guest_id: number;
  segment_name: SegmentName;
  assigned_at: string;
}

export interface EmailCampaign {
  campaign_id: number;
  name: string;
  segment_name: SegmentName | 'all';
  subject: string;
  preview_text: string | null;
  body: string;
  from_email: string;
  from_name: string;
  status: CampaignStatus;
  recipient_count: number;
  scheduled_at: string | null;
  sent_at: string | null;
  created_at: string;
}

export interface CampaignSend {
  send_id: number;
  campaign_id: number;
  guest_id: number;
  email: string;
  status: CampaignSendStatus;
  sent_at: string | null;
  opened_at: string | null;
  clicked_at: string | null;
}

export interface CampaignStats {
  campaign_id: number;
  recipient_count: number;
  sent_count: number;
  delivered_count: number;
  opened_count: number;
  clicked_count: number;
  open_rate: number;                    // 0–1 decimal
  click_rate: number;                   // 0–1 decimal
}

// ------------------------------------------------------------------
// Sync / system
// ------------------------------------------------------------------

export interface SyncStatusRecord {
  status: SyncStatus;
  last_sync_at: string | null;         // ISO datetime string
  last_sync_records: number | null;
  last_error: string | null;
  next_sync_at: string | null;
}

export interface CRMAuditLog {
  audit_id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  actor: string;
  invariant_checked: string | null;
  result: 'pass' | 'fail';
  created_at: string;
}

// ------------------------------------------------------------------
// API request shapes (what the frontend sends to the backend)
// ------------------------------------------------------------------

export interface NoteCreate {
  note_type: NoteType;
  note_text: string;
  visibility: NoteVisibility;
}

export interface PreferencesUpdate {
  room_preference: string | null;
  dietary_restrictions: string | null;
  special_occasions: string | null;
  other_notes: string | null;
}

export interface CampaignCreate {
  name: string;
  segment_name: SegmentName | 'all';
  subject: string;
  preview_text: string | null;
  body: string;
  from_email: string;
  from_name: string;
}

// ------------------------------------------------------------------
// API response shapes (what the backend returns)
// ------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type GuestListResponse = PaginatedResponse<CRMGuest>;

export interface GuestDetailResponse {
  guest: CRMGuest;
  stays: CRMStay[];
  notes: GuestNote[];
  preferences: GuestPreference | null;
}

export interface SegmentSummary {
  segment_name: SegmentName;
  label: string;
  description: string;
  criteria: string;
  guest_count: number;
}

export interface AnalyticsSummary {
  total_guests: number;
  repeat_guest_rate: number;           // 0–1 decimal
  avg_ltv: number;
  avg_stays_per_guest: number;
  active_campaigns: number;
  guests_synced_today: number;
}

export interface LTVBucket {
  label: string;                       // e.g. "$0–200"
  min: number;
  max: number | null;
  count: number;
}

export interface RetentionPoint {
  month: string;                       // e.g. "2025-09"
  repeat_rate: number;                 // 0–1 decimal
  total_guests: number;
  repeat_guests: number;
}

// ------------------------------------------------------------------
// UI-only types (not sent to/from API)
// ------------------------------------------------------------------

export interface GuestListFilters {
  search: string;
  segment: SegmentName | 'all' | null;
  loyalty_tier: LoyaltyTier | null;
  sort_field: 'name' | 'last_stay_date' | 'total_revenue_lifetime' | 'total_stays_count';
  sort_dir: 'asc' | 'desc';
  page: number;
}

export const SEGMENT_META: Record<SegmentName, { label: string; description: string; criteria: string; emoji: string }> = {
  vip: {
    label: 'VIP',
    description: 'Top 10% by lifetime revenue',
    criteria: 'Lifetime revenue > 90th percentile',
    emoji: '💎',
  },
  repeat: {
    label: 'Repeat Guests',
    description: 'Loyal customers who return',
    criteria: '2 or more stays',
    emoji: '🔁',
  },
  first_time: {
    label: 'First-Time Guests',
    description: 'Only 1 stay — potential for more',
    criteria: 'Exactly 1 stay',
    emoji: '🆕',
  },
  inactive: {
    label: 'Inactive',
    description: "Haven't visited recently",
    criteria: 'Last stay more than 180 days ago',
    emoji: '😴',
  },
  high_spender: {
    label: 'High Spenders',
    description: 'Above-average spend per stay',
    criteria: 'Average revenue per stay > $500',
    emoji: '💰',
  },
  frequent: {
    label: 'Frequent Guests',
    description: 'Guests who visit often',
    criteria: '6 or more stays',
    emoji: '⭐',
  },
};