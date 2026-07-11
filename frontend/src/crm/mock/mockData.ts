// ============================================================
// CRM Mock Data — Phase 1 Development
// ============================================================
// Used by crmClient.ts when VITE_CRM_USE_MOCK=true (Phase 1)
// Replaced by real API calls in Phase 2.
//
// 30 guests, realistic stay history, notes for ~40% of guests.
// Data satisfies all CRM TypeScript interfaces in crm/types/crm.ts
// ============================================================

import type {
  CRMGuest,
  CRMStay,
  GuestNote,
  GuestPreference,
  EmailCampaign,
  SegmentSummary,
  AnalyticsSummary,
  LTVBucket,
  RetentionPoint,
  SyncStatusRecord,
} from '../types/crm';

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

function isoDate(daysAgo: number): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString().split('T')[0];
}

function isoDateTime(daysAgo: number): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString();
}

function avgRevenue(guest: Omit<CRMGuest, 'avg_revenue_per_stay' | 'full_name' | 'segments'>): number {
  if (guest.total_stays_count === 0) return 0;
  return Math.round((guest.total_revenue_lifetime / guest.total_stays_count) * 100) / 100;
}

// ------------------------------------------------------------------
// Guests (30)
// ------------------------------------------------------------------

const rawGuests: Omit<CRMGuest, 'avg_revenue_per_stay' | 'full_name' | 'segments'>[] = [
  { guest_id: 1,  first_name: 'James',    last_name: 'Harrington', email: 'j.harrington@example.com',  phone: '+1-415-555-0101', country: 'US', loyalty_tier: 'platinum', registration_date: isoDate(730), total_stays_count: 14, total_revenue_lifetime: 8240.50, last_stay_date: isoDate(12),  is_vip: true,  is_repeat: true,  is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(730), pms_updated_at: isoDateTime(12),  crm_synced_at: isoDateTime(0) },
  { guest_id: 2,  first_name: 'Sophia',   last_name: 'Laurent',    email: 'sophia.laurent@example.com', phone: '+33-1-5550-0202', country: 'FR', loyalty_tier: 'gold',     registration_date: isoDate(540), total_stays_count: 9,  total_revenue_lifetime: 5120.00, last_stay_date: isoDate(30),  is_vip: true,  is_repeat: true,  is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(540), pms_updated_at: isoDateTime(30),  crm_synced_at: isoDateTime(0) },
  { guest_id: 3,  first_name: 'Marcus',   last_name: 'Chen',       email: 'marcus.chen@example.com',    phone: '+44-20-5550-0303', country: 'GB', loyalty_tier: 'gold',     registration_date: isoDate(480), total_stays_count: 7,  total_revenue_lifetime: 4380.75, last_stay_date: isoDate(45),  is_vip: true,  is_repeat: true,  is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(480), pms_updated_at: isoDateTime(45),  crm_synced_at: isoDateTime(0) },
  { guest_id: 4,  first_name: 'Aisha',    last_name: 'Patel',      email: 'aisha.patel@example.com',    phone: '+1-212-555-0404', country: 'US', loyalty_tier: 'gold',     registration_date: isoDate(400), total_stays_count: 6,  total_revenue_lifetime: 3960.00, last_stay_date: isoDate(8),   is_vip: true,  is_repeat: true,  is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(400), pms_updated_at: isoDateTime(8),   crm_synced_at: isoDateTime(0) },
  { guest_id: 5,  first_name: 'Thomas',   last_name: 'Weber',      email: 'thomas.weber@example.com',   phone: '+49-30-5550-0505', country: 'DE', loyalty_tier: 'silver',   registration_date: isoDate(365), total_stays_count: 5,  total_revenue_lifetime: 2890.50, last_stay_date: isoDate(60),  is_vip: false, is_repeat: true,  is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(365), pms_updated_at: isoDateTime(60),  crm_synced_at: isoDateTime(0) },
  { guest_id: 6,  first_name: 'Elena',    last_name: 'Russo',      email: 'elena.russo@example.com',    phone: '+39-06-5550-0606', country: 'IT', loyalty_tier: 'platinum', registration_date: isoDate(600), total_stays_count: 11, total_revenue_lifetime: 7650.25, last_stay_date: isoDate(5),   is_vip: true,  is_repeat: true,  is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(600), pms_updated_at: isoDateTime(5),   crm_synced_at: isoDateTime(0) },
  { guest_id: 7,  first_name: 'David',    last_name: 'Kim',        email: 'david.kim@example.com',      phone: '+82-2-5550-0707',  country: 'KR', loyalty_tier: 'silver',   registration_date: isoDate(300), total_stays_count: 4,  total_revenue_lifetime: 1840.00, last_stay_date: isoDate(185), is_vip: false, is_repeat: true,  is_inactive: true,  is_high_spender: false, pms_created_at: isoDateTime(300), pms_updated_at: isoDateTime(185), crm_synced_at: isoDateTime(0) },
  { guest_id: 8,  first_name: 'Maria',    last_name: 'Santos',     email: 'maria.santos@example.com',   phone: '+55-11-5550-0808', country: 'BR', loyalty_tier: 'bronze',   registration_date: isoDate(250), total_stays_count: 3,  total_revenue_lifetime: 1120.50, last_stay_date: isoDate(110), is_vip: false, is_repeat: true,  is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(250), pms_updated_at: isoDateTime(110), crm_synced_at: isoDateTime(0) },
  { guest_id: 9,  first_name: 'Ahmed',    last_name: 'Al-Rashid',  email: 'ahmed.alrashid@example.com', phone: '+971-4-5550-0909', country: 'AE', loyalty_tier: 'gold',     registration_date: isoDate(420), total_stays_count: 8,  total_revenue_lifetime: 6200.00, last_stay_date: isoDate(22),  is_vip: true,  is_repeat: true,  is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(420), pms_updated_at: isoDateTime(22),  crm_synced_at: isoDateTime(0) },
  { guest_id: 10, first_name: 'Yuki',     last_name: 'Tanaka',     email: 'yuki.tanaka@example.com',    phone: '+81-3-5550-1010',  country: 'JP', loyalty_tier: 'silver',   registration_date: isoDate(200), total_stays_count: 3,  total_revenue_lifetime: 980.75,  last_stay_date: isoDate(150), is_vip: false, is_repeat: true,  is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(200), pms_updated_at: isoDateTime(150), crm_synced_at: isoDateTime(0) },
  { guest_id: 11, first_name: 'Claire',   last_name: 'Dubois',     email: 'claire.dubois@example.com',  phone: '+33-1-5550-1111',  country: 'FR', loyalty_tier: 'bronze',   registration_date: isoDate(180), total_stays_count: 2,  total_revenue_lifetime: 640.00,  last_stay_date: isoDate(200), is_vip: false, is_repeat: true,  is_inactive: true,  is_high_spender: false, pms_created_at: isoDateTime(180), pms_updated_at: isoDateTime(200), crm_synced_at: isoDateTime(0) },
  { guest_id: 12, first_name: 'Robert',   last_name: 'Mitchell',   email: 'r.mitchell@example.com',     phone: '+1-617-555-1212',  country: 'US', loyalty_tier: 'bronze',   registration_date: isoDate(120), total_stays_count: 1,  total_revenue_lifetime: 310.00,  last_stay_date: isoDate(120), is_vip: false, is_repeat: false, is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(120), pms_updated_at: isoDateTime(120), crm_synced_at: isoDateTime(0) },
  { guest_id: 13, first_name: 'Priya',    last_name: 'Sharma',     email: 'priya.sharma@example.com',   phone: '+91-22-5550-1313', country: 'IN', loyalty_tier: 'silver',   registration_date: isoDate(310), total_stays_count: 4,  total_revenue_lifetime: 1560.50, last_stay_date: isoDate(75),  is_vip: false, is_repeat: true,  is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(310), pms_updated_at: isoDateTime(75),  crm_synced_at: isoDateTime(0) },
  { guest_id: 14, first_name: 'Lucas',    last_name: 'Fernandez',  email: 'lucas.fernandez@example.com', phone: '+34-91-555-1414', country: 'ES', loyalty_tier: 'bronze',   registration_date: isoDate(90),  total_stays_count: 1,  total_revenue_lifetime: 490.00,  last_stay_date: isoDate(90),  is_vip: false, is_repeat: false, is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(90),  pms_updated_at: isoDateTime(90),  crm_synced_at: isoDateTime(0) },
  { guest_id: 15, first_name: 'Ingrid',   last_name: 'Berg',       email: 'ingrid.berg@example.com',    phone: '+47-22-555-1515',  country: 'NO', loyalty_tier: 'bronze',   registration_date: isoDate(220), total_stays_count: 2,  total_revenue_lifetime: 870.25,  last_stay_date: isoDate(220), is_vip: false, is_repeat: true,  is_inactive: true,  is_high_spender: false, pms_created_at: isoDateTime(220), pms_updated_at: isoDateTime(220), crm_synced_at: isoDateTime(0) },
  { guest_id: 16, first_name: 'Carlos',   last_name: 'Mendoza',    email: 'carlos.mendoza@example.com', phone: '+52-55-5550-1616', country: 'MX', loyalty_tier: 'bronze',   registration_date: isoDate(50),  total_stays_count: 1,  total_revenue_lifetime: 275.00,  last_stay_date: isoDate(50),  is_vip: false, is_repeat: false, is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(50),  pms_updated_at: isoDateTime(50),  crm_synced_at: isoDateTime(0) },
  { guest_id: 17, first_name: 'Fatima',   last_name: 'Hassan',     email: 'fatima.hassan@example.com',  phone: '+20-2-5550-1717',  country: 'EG', loyalty_tier: 'bronze',   registration_date: isoDate(40),  total_stays_count: 1,  total_revenue_lifetime: 395.50,  last_stay_date: isoDate(40),  is_vip: false, is_repeat: false, is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(40),  pms_updated_at: isoDateTime(40),  crm_synced_at: isoDateTime(0) },
  { guest_id: 18, first_name: 'William',  last_name: 'Clarke',     email: 'w.clarke@example.com',       phone: '+61-2-5550-1818',  country: 'AU', loyalty_tier: 'silver',   registration_date: isoDate(280), total_stays_count: 3,  total_revenue_lifetime: 1380.00, last_stay_date: isoDate(280), is_vip: false, is_repeat: true,  is_inactive: true,  is_high_spender: false, pms_created_at: isoDateTime(280), pms_updated_at: isoDateTime(280), crm_synced_at: isoDateTime(0) },
  { guest_id: 19, first_name: 'Nadia',    last_name: 'Kovač',      email: 'nadia.kovac@example.com',    phone: '+385-1-5550-1919', country: 'HR', loyalty_tier: 'bronze',   registration_date: isoDate(30),  total_stays_count: 1,  total_revenue_lifetime: 520.00,  last_stay_date: isoDate(30),  is_vip: false, is_repeat: false, is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(30),  pms_updated_at: isoDateTime(30),  crm_synced_at: isoDateTime(0) },
  { guest_id: 20, first_name: 'Henrik',   last_name: 'Lindström',  email: 'h.lindstrom@example.com',    phone: '+46-8-5550-2020',  country: 'SE', loyalty_tier: 'silver',   registration_date: isoDate(340), total_stays_count: 5,  total_revenue_lifetime: 2340.75, last_stay_date: isoDate(100), is_vip: false, is_repeat: true,  is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(340), pms_updated_at: isoDateTime(100), crm_synced_at: isoDateTime(0) },
  { guest_id: 21, first_name: 'Diana',    last_name: 'Okonkwo',    email: 'diana.okonkwo@example.com',  phone: '+234-1-5550-2121', country: 'NG', loyalty_tier: 'bronze',   registration_date: isoDate(25),  total_stays_count: 1,  total_revenue_lifetime: 450.00,  last_stay_date: isoDate(25),  is_vip: false, is_repeat: false, is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(25),  pms_updated_at: isoDateTime(25),  crm_synced_at: isoDateTime(0) },
  { guest_id: 22, first_name: 'Patrick',  last_name: "O'Brien",    email: 'p.obrien@example.com',       phone: '+353-1-5550-2222', country: 'IE', loyalty_tier: 'silver',   registration_date: isoDate(260), total_stays_count: 4,  total_revenue_lifetime: 1760.50, last_stay_date: isoDate(55),  is_vip: false, is_repeat: true,  is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(260), pms_updated_at: isoDateTime(55),  crm_synced_at: isoDateTime(0) },
  { guest_id: 23, first_name: 'Mei',      last_name: 'Zhang',      email: 'mei.zhang@example.com',      phone: '+86-10-5550-2323', country: 'CN', loyalty_tier: 'gold',     registration_date: isoDate(450), total_stays_count: 7,  total_revenue_lifetime: 3870.00, last_stay_date: isoDate(18),  is_vip: true,  is_repeat: true,  is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(450), pms_updated_at: isoDateTime(18),  crm_synced_at: isoDateTime(0) },
  { guest_id: 24, first_name: 'Giorgio',  last_name: 'Bianchi',    email: 'g.bianchi@example.com',      phone: '+39-02-5550-2424', country: 'IT', loyalty_tier: 'bronze',   registration_date: isoDate(70),  total_stays_count: 1,  total_revenue_lifetime: 680.00,  last_stay_date: isoDate(70),  is_vip: false, is_repeat: false, is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(70),  pms_updated_at: isoDateTime(70),  crm_synced_at: isoDateTime(0) },
  { guest_id: 25, first_name: 'Rachel',   last_name: 'Goldstein',  email: 'r.goldstein@example.com',    phone: '+1-305-555-2525',  country: 'US', loyalty_tier: 'silver',   registration_date: isoDate(190), total_stays_count: 2,  total_revenue_lifetime: 920.50,  last_stay_date: isoDate(190), is_vip: false, is_repeat: true,  is_inactive: true,  is_high_spender: false, pms_created_at: isoDateTime(190), pms_updated_at: isoDateTime(190), crm_synced_at: isoDateTime(0) },
  { guest_id: 26, first_name: 'Ivan',     last_name: 'Petrov',     email: 'ivan.petrov@example.com',    phone: '+7-495-5550-2626', country: 'RU', loyalty_tier: 'bronze',   registration_date: isoDate(60),  total_stays_count: 1,  total_revenue_lifetime: 340.00,  last_stay_date: isoDate(60),  is_vip: false, is_repeat: false, is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(60),  pms_updated_at: isoDateTime(60),  crm_synced_at: isoDateTime(0) },
  { guest_id: 27, first_name: 'Amelia',   last_name: 'Thompson',   email: 'a.thompson@example.com',     phone: '+1-416-555-2727',  country: 'CA', loyalty_tier: 'silver',   registration_date: isoDate(230), total_stays_count: 3,  total_revenue_lifetime: 1250.00, last_stay_date: isoDate(230), is_vip: false, is_repeat: true,  is_inactive: true,  is_high_spender: false, pms_created_at: isoDateTime(230), pms_updated_at: isoDateTime(230), crm_synced_at: isoDateTime(0) },
  { guest_id: 28, first_name: 'Ravi',     last_name: 'Krishnamurthy', email: 'ravi.k@example.com',     phone: '+65-6-5550-2828',  country: 'SG', loyalty_tier: 'gold',     registration_date: isoDate(380), total_stays_count: 5,  total_revenue_lifetime: 3540.25, last_stay_date: isoDate(35),  is_vip: true,  is_repeat: true,  is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(380), pms_updated_at: isoDateTime(35),  crm_synced_at: isoDateTime(0) },
  { guest_id: 29, first_name: 'Charlotte', last_name: 'Beaumont',  email: 'c.beaumont@example.com',     phone: '+32-2-5550-2929',  country: 'BE', loyalty_tier: 'bronze',   registration_date: isoDate(15),  total_stays_count: 1,  total_revenue_lifetime: 285.00,  last_stay_date: isoDate(15),  is_vip: false, is_repeat: false, is_inactive: false, is_high_spender: false, pms_created_at: isoDateTime(15),  pms_updated_at: isoDateTime(15),  crm_synced_at: isoDateTime(0) },
  { guest_id: 30, first_name: 'Hassan',   last_name: 'Al-Farsi',   email: 'h.alfarsi@example.com',      phone: '+968-2-5550-3030', country: 'OM', loyalty_tier: 'gold',     registration_date: isoDate(500), total_stays_count: 8,  total_revenue_lifetime: 5780.00, last_stay_date: isoDate(3),   is_vip: true,  is_repeat: true,  is_inactive: false, is_high_spender: true,  pms_created_at: isoDateTime(500), pms_updated_at: isoDateTime(3),   crm_synced_at: isoDateTime(0) },
];

function deriveSegments(g: Omit<CRMGuest, 'avg_revenue_per_stay' | 'full_name' | 'segments'>): import('../types/crm').SegmentName[] {
  const segments: import('../types/crm').SegmentName[] = [];
  if (g.is_vip) segments.push('vip');
  if (g.total_stays_count >= 6) segments.push('frequent');
  if (g.total_stays_count >= 2) segments.push('repeat');
  if (g.total_stays_count === 1) segments.push('first_time');
  if (g.is_inactive) segments.push('inactive');
  if (g.is_high_spender) segments.push('high_spender');
  return segments;
}

export const MOCK_GUESTS: CRMGuest[] = rawGuests.map(g => ({
  ...g,
  full_name: `${g.first_name} ${g.last_name}`,
  avg_revenue_per_stay: avgRevenue(g),
  segments: deriveSegments(g),
}));

// ------------------------------------------------------------------
// Stays (3–14 per VIP guest, 1–3 per others — abbreviated set)
// ------------------------------------------------------------------

export const MOCK_STAYS: CRMStay[] = [
  // Guest 1 — James Harrington (14 stays)
  { stay_id: 101, guest_id: 1, reservation_id: 1001, room_number: '501', check_in_date: isoDate(12),  check_out_date: isoDate(9),   nights: 3, status: 'checked_out', total_revenue: 1240.00, room_revenue: 1050.00, other_revenue: 190.00, crm_synced_at: isoDateTime(0) },
  { stay_id: 102, guest_id: 1, reservation_id: 1002, room_number: '305', check_in_date: isoDate(95),  check_out_date: isoDate(92),  nights: 3, status: 'checked_out', total_revenue: 890.50,  room_revenue: 780.00,  other_revenue: 110.50, crm_synced_at: isoDateTime(0) },
  { stay_id: 103, guest_id: 1, reservation_id: 1003, room_number: '501', check_in_date: isoDate(200), check_out_date: isoDate(195), nights: 5, status: 'checked_out', total_revenue: 1480.00, room_revenue: 1300.00, other_revenue: 180.00, crm_synced_at: isoDateTime(0) },
  // Guest 2 — Sophia Laurent (9 stays)
  { stay_id: 201, guest_id: 2, reservation_id: 2001, room_number: '402', check_in_date: isoDate(30),  check_out_date: isoDate(27),  nights: 3, status: 'checked_out', total_revenue: 760.00,  room_revenue: 680.00,  other_revenue: 80.00,  crm_synced_at: isoDateTime(0) },
  { stay_id: 202, guest_id: 2, reservation_id: 2002, room_number: '402', check_in_date: isoDate(120), check_out_date: isoDate(118), nights: 2, status: 'checked_out', total_revenue: 520.00,  room_revenue: 480.00,  other_revenue: 40.00,  crm_synced_at: isoDateTime(0) },
  // Guest 6 — Elena Russo (11 stays)
  { stay_id: 601, guest_id: 6, reservation_id: 6001, room_number: '301', check_in_date: isoDate(5),   check_out_date: isoDate(3),   nights: 2, status: 'checked_out', total_revenue: 920.00,  room_revenue: 800.00,  other_revenue: 120.00, crm_synced_at: isoDateTime(0) },
  { stay_id: 602, guest_id: 6, reservation_id: 6002, room_number: '501', check_in_date: isoDate(80),  check_out_date: isoDate(74),  nights: 6, status: 'checked_out', total_revenue: 2100.00, room_revenue: 1800.00, other_revenue: 300.00, crm_synced_at: isoDateTime(0) },
  // Guest 9 — Ahmed Al-Rashid (8 stays)
  { stay_id: 901, guest_id: 9, reservation_id: 9001, room_number: '601', check_in_date: isoDate(22),  check_out_date: isoDate(18),  nights: 4, status: 'checked_out', total_revenue: 1640.00, room_revenue: 1440.00, other_revenue: 200.00, crm_synced_at: isoDateTime(0) },
  // Guest 30 — Hassan Al-Farsi (8 stays)
  { stay_id: 3001, guest_id: 30, reservation_id: 3001, room_number: '702', check_in_date: isoDate(3),  check_out_date: isoDate(1),  nights: 2, status: 'checked_out', total_revenue: 980.00,  room_revenue: 880.00,  other_revenue: 100.00, crm_synced_at: isoDateTime(0) },
  // Guest 12 — Robert Mitchell (1 stay, first-time)
  { stay_id: 1201, guest_id: 12, reservation_id: 1201, room_number: '204', check_in_date: isoDate(120), check_out_date: isoDate(118), nights: 2, status: 'checked_out', total_revenue: 310.00, room_revenue: 290.00, other_revenue: 20.00, crm_synced_at: isoDateTime(0) },
  // Guest 16 — Carlos Mendoza (1 stay, first-time)
  { stay_id: 1601, guest_id: 16, reservation_id: 1601, room_number: '108', check_in_date: isoDate(50), check_out_date: isoDate(49), nights: 1, status: 'checked_out', total_revenue: 275.00, room_revenue: 260.00, other_revenue: 15.00, crm_synced_at: isoDateTime(0) },
];

// ------------------------------------------------------------------
// Notes (~40% of guests)
// ------------------------------------------------------------------

export const MOCK_NOTES: GuestNote[] = [
  { note_id: 1,  guest_id: 1,  note_type: 'vip',              note_text: 'VIP guest — ensure complimentary upgrade to suite when available. Repeat platinum member, always books direct.', visibility: 'internal', author: 'Maria Rodriguez', created_at: isoDateTime(12) },
  { note_id: 2,  guest_id: 1,  note_type: 'preference',       note_text: 'Prefers high floor, quiet room away from elevator. Always requests extra pillows (2 additional). Hypoallergenic bedding required.', visibility: 'internal', author: 'David Park', created_at: isoDateTime(95) },
  { note_id: 3,  guest_id: 2,  note_type: 'preference',       note_text: 'Vegetarian — ensure breakfast options clearly labelled. Prefers late check-in after 4pm when possible.', visibility: 'internal', author: 'Maria Rodriguez', created_at: isoDateTime(30) },
  { note_id: 4,  guest_id: 3,  note_type: 'issue',            note_text: 'Guest complained about noise from neighbouring room on last stay (Room 402). Ensure room assignment avoids that wing.', visibility: 'internal', author: 'Jennifer Chen', created_at: isoDateTime(45) },
  { note_id: 5,  guest_id: 4,  note_type: 'preference',       note_text: 'Prefers room 402 or similar corner rooms on 4th floor. Twin beds preferred over double.', visibility: 'internal', author: 'Maria Rodriguez', created_at: isoDateTime(8) },
  { note_id: 6,  guest_id: 6,  note_type: 'vip',              note_text: 'Platinum member — complimentary fruit basket and bottle of prosecco on arrival. Personal note from GM requested on extended stays.', visibility: 'internal', author: 'David Park', created_at: isoDateTime(5) },
  { note_id: 7,  guest_id: 9,  note_type: 'special_request',  note_text: 'Guest often travels for business, requires early check-in (before 10am) and late checkout (after 2pm). Both accommodated on last 3 stays.', visibility: 'internal', author: 'Jennifer Chen', created_at: isoDateTime(22) },
  { note_id: 8,  guest_id: 13, note_type: 'preference',       note_text: 'Gluten-free dietary requirement. Please ensure restaurant and room service are notified for any F&B orders.', visibility: 'internal', author: 'Maria Rodriguez', created_at: isoDateTime(75) },
  { note_id: 9,  guest_id: 20, note_type: 'general',          note_text: 'Guest mentioned they are celebrating their 10th wedding anniversary on the next visit. Coordinate with F&B for a surprise dessert.', visibility: 'internal', author: 'David Park', created_at: isoDateTime(100) },
  { note_id: 10, guest_id: 23, note_type: 'preference',       note_text: 'Mandarin-speaking guest — front desk to greet in Mandarin when possible. Prefers high floor with city view.', visibility: 'internal', author: 'Jennifer Chen', created_at: isoDateTime(18) },
  { note_id: 11, guest_id: 28, note_type: 'vip',              note_text: 'Corporate account holder — all stays billed to account SG-CORP-441. Provide itemised receipt on checkout.', visibility: 'internal', author: 'David Park', created_at: isoDateTime(35) },
  { note_id: 12, guest_id: 30, note_type: 'vip',              note_text: 'Returning VIP — guest has referred 3 new guests this year. Loyalty reward pending (GM approval). Prefers Suite 702 exclusively.', visibility: 'internal', author: 'David Park', created_at: isoDateTime(3) },
];

// ------------------------------------------------------------------
// Preferences
// ------------------------------------------------------------------

export const MOCK_PREFERENCES: GuestPreference[] = [
  { preference_id: 1, guest_id: 1,  room_preference: 'High floor (5th+), quiet, suite preferred', dietary_restrictions: 'Hypoallergenic bedding required', special_occasions: 'Wedding anniversary: October 14', other_notes: null, updated_at: isoDateTime(12) },
  { preference_id: 2, guest_id: 2,  room_preference: 'Upper floors, city view', dietary_restrictions: 'Vegetarian', special_occasions: null, other_notes: 'Late check-in preferred', updated_at: isoDateTime(30) },
  { preference_id: 3, guest_id: 4,  room_preference: 'Room 402 or corner room, 4th floor, twin beds', dietary_restrictions: null, special_occasions: null, other_notes: null, updated_at: isoDateTime(8) },
  { preference_id: 4, guest_id: 6,  room_preference: 'Suite only', dietary_restrictions: null, special_occasions: 'Birthday: March 22', other_notes: 'Complimentary prosecco on arrival per platinum policy', updated_at: isoDateTime(5) },
  { preference_id: 5, guest_id: 9,  room_preference: 'Business floor, quiet, work desk essential', dietary_restrictions: null, special_occasions: null, other_notes: 'Early check-in and late checkout standard', updated_at: isoDateTime(22) },
  { preference_id: 6, guest_id: 13, room_preference: null, dietary_restrictions: 'Gluten-free', special_occasions: null, other_notes: null, updated_at: isoDateTime(75) },
  { preference_id: 7, guest_id: 23, room_preference: 'High floor, city view', dietary_restrictions: null, special_occasions: null, other_notes: 'Mandarin greeting appreciated', updated_at: isoDateTime(18) },
  { preference_id: 8, guest_id: 30, room_preference: 'Suite 702 exclusively', dietary_restrictions: null, special_occasions: null, other_notes: 'Corporate billing: SG-CORP-441', updated_at: isoDateTime(3) },
];

// ------------------------------------------------------------------
// Campaigns (mock history)
// ------------------------------------------------------------------

export const MOCK_CAMPAIGNS: EmailCampaign[] = [
  {
    campaign_id: 1,
    name: 'VIP 20% Off — Spring 2026',
    segment_name: 'vip',
    subject: 'Exclusive VIP Offer: 20% Off Your Next Stay',
    preview_text: 'As one of our most valued guests, we have a special offer for you.',
    body: 'Dear {first_name},\n\nAs one of our most valued VIP guests, we are delighted to offer you an exclusive 20% discount on your next stay.\n\nUse code VIP20 when booking before March 31, 2026.\n\nWe look forward to welcoming you back.\n\nWarm regards,\nThe Team',
    from_email: 'marketing@hotel.com',
    from_name: 'Hotel Marketing Team',
    status: 'sent',
    recipient_count: 9,
    scheduled_at: null,
    sent_at: isoDateTime(20),
    created_at: isoDateTime(21),
  },
  {
    campaign_id: 2,
    name: 'We Miss You — Inactive Guests',
    segment_name: 'inactive',
    subject: 'We miss you — come back for a special rate',
    preview_text: 'It has been a while since your last visit.',
    body: 'Dear {first_name},\n\nWe noticed it has been a while since your last stay and we miss having you with us.\n\nTo welcome you back, we are offering you a 15% discount on your next visit. No code needed — just mention this email at check-in.\n\nOffer valid through April 30, 2026.\n\nSee you soon.',
    from_email: 'marketing@hotel.com',
    from_name: 'Hotel Marketing Team',
    status: 'draft',
    recipient_count: 6,
    scheduled_at: null,
    sent_at: null,
    created_at: isoDateTime(2),
  },
];

// ------------------------------------------------------------------
// Segment summaries
// ------------------------------------------------------------------

export const MOCK_SEGMENT_SUMMARIES: SegmentSummary[] = [
  { segment_name: 'vip',          label: 'VIP',             description: 'Top 10% by lifetime revenue',      criteria: 'Lifetime revenue > 90th percentile', guest_count: MOCK_GUESTS.filter(g => g.is_vip).length },
  { segment_name: 'repeat',       label: 'Repeat Guests',   description: 'Loyal customers who return',       criteria: '2 or more stays',                    guest_count: MOCK_GUESTS.filter(g => g.is_repeat).length },
  { segment_name: 'first_time',   label: 'First-Time',      description: 'Only 1 stay — potential for more', criteria: 'Exactly 1 stay',                     guest_count: MOCK_GUESTS.filter(g => g.total_stays_count === 1).length },
  { segment_name: 'inactive',     label: 'Inactive',        description: "Haven't visited in 6+ months",     criteria: 'Last stay > 180 days ago',            guest_count: MOCK_GUESTS.filter(g => g.is_inactive).length },
  { segment_name: 'high_spender', label: 'High Spenders',   description: 'Above-average spend per stay',     criteria: 'Avg revenue per stay > $500',         guest_count: MOCK_GUESTS.filter(g => g.is_high_spender).length },
  { segment_name: 'frequent',     label: 'Frequent Guests', description: 'Guests who visit most often',      criteria: '6 or more stays',                    guest_count: MOCK_GUESTS.filter(g => g.total_stays_count >= 6).length },
];

// ------------------------------------------------------------------
// Analytics
// ------------------------------------------------------------------

export const MOCK_ANALYTICS_SUMMARY: AnalyticsSummary = {
  total_guests: MOCK_GUESTS.length,
  repeat_guest_rate: MOCK_GUESTS.filter(g => g.is_repeat).length / MOCK_GUESTS.length,
  avg_ltv: Math.round(MOCK_GUESTS.reduce((s, g) => s + g.total_revenue_lifetime, 0) / MOCK_GUESTS.length),
  avg_stays_per_guest: Math.round((MOCK_GUESTS.reduce((s, g) => s + g.total_stays_count, 0) / MOCK_GUESTS.length) * 10) / 10,
  active_campaigns: MOCK_CAMPAIGNS.filter(c => c.status === 'draft').length,
  guests_synced_today: 4,
};

export const MOCK_LTV_BUCKETS: LTVBucket[] = [
  { label: '$0–$500',    min: 0,    max: 500,   count: MOCK_GUESTS.filter(g => g.total_revenue_lifetime <= 500).length },
  { label: '$500–$1k',   min: 500,  max: 1000,  count: MOCK_GUESTS.filter(g => g.total_revenue_lifetime > 500 && g.total_revenue_lifetime <= 1000).length },
  { label: '$1k–$2.5k',  min: 1000, max: 2500,  count: MOCK_GUESTS.filter(g => g.total_revenue_lifetime > 1000 && g.total_revenue_lifetime <= 2500).length },
  { label: '$2.5k–$5k',  min: 2500, max: 5000,  count: MOCK_GUESTS.filter(g => g.total_revenue_lifetime > 2500 && g.total_revenue_lifetime <= 5000).length },
  { label: '$5k+',       min: 5000, max: null,   count: MOCK_GUESTS.filter(g => g.total_revenue_lifetime > 5000).length },
];

export const MOCK_RETENTION_POINTS: RetentionPoint[] = [
  { month: '2025-09', repeat_rate: 0.41, total_guests: 22, repeat_guests: 9 },
  { month: '2025-10', repeat_rate: 0.44, total_guests: 25, repeat_guests: 11 },
  { month: '2025-11', repeat_rate: 0.38, total_guests: 21, repeat_guests: 8 },
  { month: '2025-12', repeat_rate: 0.52, total_guests: 29, repeat_guests: 15 },
  { month: '2026-01', repeat_rate: 0.48, total_guests: 27, repeat_guests: 13 },
  { month: '2026-02', repeat_rate: 0.50, total_guests: 30, repeat_guests: 15 },
];

export const MOCK_SYNC_STATUS: SyncStatusRecord = {
  status: 'success',
  last_sync_at: isoDateTime(0),
  last_sync_records: 4,
  last_error: null,
  next_sync_at: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
};