/**
 * API Type Definitions
 * Generated from backend API schemas
 */

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

// Guest types
export interface Guest {
  id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  guest_type: string;
  is_vip: boolean;
  total_stays: number;
  total_nights: number;
}

export interface GuestCreate {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  guest_type?: string;
}

export interface GuestUpdate {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  special_requests?: string;
}

// Reservation types
export interface Reservation {
  id: number;
  confirmation_number: string;
  property_id: number;
  guest_id: number;
  room_type_id: number;
  check_in_date: string;
  check_out_date: string;
  number_of_nights: number;
  num_adults: number;
  num_children: number;
  status: string;
  total_amount: number;
  nightly_rate: number;
  created_at: string;
}

export interface ReservationCreate {
  property_id: number;
  guest_id: number;
  room_type_id: number;
  check_in_date: string;
  check_out_date: string;
  num_adults: number;
  num_children?: number;
  rate_plan_id?: number;
  nightly_rate?: number;
  source?: string;
  special_requests?: string;
}

export interface ReservationUpdate {
  check_in_date?: string;
  check_out_date?: string;
  num_adults?: number;
  num_children?: number;
  special_requests?: string;
}

// Room types
export interface Room {
  id: number;
  property_id: number;
  room_type_id: number;
  room_number: string;
  floor: number | null;
  building: string | null;
  occupancy_state: 'vacant' | 'occupied' | string;
  condition_state: 'clean' | 'dirty' | string;
  is_active: boolean;
  is_available: boolean;
  current_guest?: string;
  current_reservation?: string;
  current_reservation_id?: number;
}

// Stay types
export interface Stay {
  id: number;
  reservation_id: number;
  room_id: number;
  guest_id: number;
  check_in_date: string;
  check_out_date: string;
  status: string;
  total_charges: number;
  number_of_nights: number;
}

// Charge types
export interface Charge {
  id: number;
  stay_id: number;
  charge_type: string;
  description: string;
  amount: number;
  total_amount: number;
  status: string;
  charge_date: string | null;
}

export interface ChargeCreate {
  stay_id: number;
  charge_type: string;
  description: string;
  amount: number;
  quantity?: number;
}

// Operation types
export interface CheckInRequest {
  reservation_id?: number;
  confirmation_number?: string;
  room_id?: number;
  room_number?: string;
  post_room_charges?: boolean;
}

export interface CheckInResponse {
  success: boolean;
  message: string;
  reservation: Reservation;
  room_number: string;
  charges_posted: number;
  warnings: string[];
}

export interface CheckOutRequest {
  stay_id?: number;
  reservation_id?: number;
  confirmation_number?: string;
  room_id?: number;
  payment_method?: string;
  force_checkout?: boolean;
}

export interface CheckOutResponse {
  success: boolean;
  message: string;
  bill: {
    stay_id: number;
    subtotal: number;
    tax: number;
    total: number;
    paid: number;
    balance: number;
    reservation: {
      guest: string;
      room: string;
      check_in: string;
      check_out: string;
      nights: number;
      confirmation: string;
    };
    charges_by_type: Record<string, {
      subtotal: number;
      items: Array<{
        description: string;
        total: number;
      }>;
    }>;
  };
  payment?: any;
  warnings: string[];
}

// API Response types
export interface ApiError {
  success: false;
  error: string;
  code: string;
  details?: any;
}

export interface SuccessResponse {
  success: true;
  message: string;
  data?: any;
}

export interface DatabaseInfo {
  version: string;
  dialect: string;
  status: string;
  pool: {
    size: number;
    active: number;
    idle: number;
  };
}

export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  services: Record<string, string>;
}

export interface DashboardStats {
  occupancy_rate: number;
  adr: number;
  revpar: number;
  arrivals_today: number;
  departures_today: number;
  stays_today: number;
  revenue_today: number;
}

export interface KPISummary {
  revenue: number;
  occupancy: number;
  adr: number;
  revpar: number;
  trends: Record<string, number[]>;
}

export interface PerformanceScorecard {
  overall_score: number;
  categories: Array<{
    name: string;
    score: number;
    trend: 'up' | 'down' | 'neutral';
  }>;
}

export interface EfficiencyMetrics {
  staff_efficiency: number;
  room_turnover_time: number;
  check_in_time: number;
  check_out_time: number;
}

export interface AuditLog {
  id: number;
  user_id: number;
  username: string;
  action: string;
  resource: string;
  resource_id: string;
  details: any;
  ip_address: string;
  created_at: string;
}

export interface ComplianceReport {
  status: 'compliant' | 'non-compliant' | 'partial';
  last_audit: string;
  issues: string[];
}

export interface SecuritySummary {
  failed_logins: number;
  active_sessions: number;
  security_alerts: number;
}

export interface RetentionStatus {
  data_retention_days: number;
  eligible_for_deletion: number;
}

export interface AuditStats {
  total_logs: number;
  logs_by_action: Record<string, number>;
}

export interface SavedSearch {
  id: number;
  name: string;
  query: string;
  filters: any;
}

export interface SearchSuggestion {
  text: string;
  type: 'guest' | 'reservation' | 'room' | 'other';
  id?: string | number;
}

export interface HousekeepingTask {
  id: number;
  room_id: number;
  room_number: string;
  task_type: string;
  status: 'pending' | 'in_progress' | 'completed' | 'on_hold';
  priority: 'low' | 'medium' | 'high';
  assigned_to?: number;
  started_at?: string;
  completed_at?: string;
}

export interface MaintenanceRequest {
  id: number;
  room_id: number;
  room_number: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_by: number;
}

export interface DailySummary {
  date: string;
  rooms_occupied: number;
  rooms_vacant: number;
  rooms_dirty: number;
  tasks_completed: number;
  pending_tasks: number;
}

export interface MonitoringMetrics {
  cpu_usage: number;
  memory_usage: number;
  active_connections: number;
  response_times: number[];
}

export interface DiscountCode {
  id: number;
  code: string;
  description: string;
  discount_type: 'percentage' | 'fixed';
  value: number;
  is_active: boolean;
  valid_from: string;
  valid_to: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  permissions?: string[];
}

export interface UserStats {
  last_login: string;
  actions_performed: number;
  active_since: string;
}

export interface UserActivity {
  timestamp: string;
  action: string;
  resource: string;
}
