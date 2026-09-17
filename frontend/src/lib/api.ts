/**
 * API Client
 * Axios-based client for backend API
 */

import axios from 'axios';
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  Guest, GuestCreate, GuestUpdate,
  Reservation, ReservationCreate, ReservationUpdate,
  Room, Stay, ChargeCreate,
  CheckInRequest, CheckInResponse,
  CheckOutRequest, CheckOutResponse,
  ApiError, SuccessResponse,
  DatabaseInfo, HealthCheckResponse, DashboardStats,
  KPISummary, PerformanceScorecard, EfficiencyMetrics,
  AuditLog, ComplianceReport, SecuritySummary,
  RetentionStatus, AuditStats, SavedSearch,
  SearchSuggestion, HousekeepingTask, MaintenanceRequest,
  DailySummary, MonitoringMetrics, DiscountCode,
  User, UserStats, UserActivity,
  LoginRequest, LoginResponse, RefreshRequest, ChangePasswordRequest
} from '@/types/api';
import { runRefresh } from '@/lib/authQueue';
import { enqueue as enqueueOfflineMutation } from '@/lib/syncQueue';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

type RetriedConfig = InternalAxiosRequestConfig & {
  _retried?: boolean;
  _queuedOffline?: boolean;
};

export interface TenantMembership {
  tenant_id: number;
  tenant_slug: string;
  tenant_name: string;
  role: string;
  is_default: boolean;
}

export interface LoginApiResponse {
  access_token: string | null;
  refresh_token: string | null;
  token_type: string;
  user: User;
  memberships: TenantMembership[];
  requires_tenant_selection: boolean;
}

export class ApiClient {
  /** Public so feature code can drop down to raw axios when no helper exists yet. */
  public readonly client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor (add auth token)
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token') || localStorage.getItem('accessToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor: 401 → refresh-and-retry (queued), then unwrap errors.
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        const status = error.response?.status;
        const originalRequest = error.config as RetriedConfig | undefined;
        const url = originalRequest?.url ?? '';

        const isAuthEndpoint =
          url.includes('/auth/refresh') ||
          url.includes('/auth/login') ||
          url.includes('/auth/select-tenant');

        if (
          status === 401 &&
          originalRequest &&
          !originalRequest._retried &&
          !isAuthEndpoint
        ) {
          originalRequest._retried = true;
          try {
            const newAccessToken = await runRefresh((rt) =>
              this.refreshAccessToken(rt)
            );
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshErr) {
            // Refresh failed; fall through to the normal rejection path so
            // the caller sees a structured error (the auth queue has
            // already cleared the session and redirected).
          }
        }

        // Offline detection: when the request never reached the server
        // (no response object) AND the browser reports offline, queue
        // mutating verbs for later replay. GETs are not queued because
        // the caller wants fresh data, not a delayed write.
        const browserOffline =
          typeof navigator !== 'undefined' && navigator.onLine === false;
        const looksLikeNetworkError = !error.response && error.code !== 'ECONNABORTED';
        const method = (originalRequest?.method ?? '').toUpperCase();
        const isMutation = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method);

        if (
          browserOffline &&
          looksLikeNetworkError &&
          isMutation &&
          originalRequest &&
          originalRequest.url &&
          !isAuthEndpoint &&
          !(originalRequest as RetriedConfig)._queuedOffline
        ) {
          (originalRequest as RetriedConfig)._queuedOffline = true;
          try {
            await enqueueOfflineMutation(
              {
                method: originalRequest.method!,
                url: originalRequest.url!,
                data: originalRequest.data,
                params: originalRequest.params as Record<string, unknown> | undefined,
              },
              `${method} ${originalRequest.url}`,
            );
            return Promise.reject({
              success: false,
              error: 'Offline — change saved locally and will sync when you reconnect.',
              code: 'OFFLINE_QUEUED',
            } as ApiError);
          } catch (queueErr) {
            // Fall through to normal error path if the queue itself failed.
          }
        }

        if (error.response?.data) {
          return Promise.reject(error.response.data);
        }

        return Promise.reject({
          success: false,
          error: error.message || 'Network error',
          code: 'NETWORK_ERROR',
        } as ApiError);
      }
    );
  }

  /** Internal: bare refresh call used by the auth queue. Returns the new
   *  access token only. Does not touch local storage — the queue does that.
   */
  private async refreshAccessToken(refreshToken: string): Promise<string> {
    // Use a dedicated axios call (not this.client) so the response
    // interceptor above doesn't recurse on a refresh failure.
    const res = await axios.post<{ access_token: string }>(
      `${API_BASE_URL}/auth/refresh`,
      { refresh_token: refreshToken },
      { headers: { 'Content-Type': 'application/json' } }
    );
    return res.data.access_token;
  }

  // =========================
  // Guest API
  // =========================

  async getGuests(params?: any): Promise<Guest[]> {
    const response = await this.client.get<Guest[]>('/guests', { params });
    return response.data;
  }

  async getGuest(id: number): Promise<Guest> {
    const response = await this.client.get<Guest>(`/guests/${id}`);
    return response.data;
  }

  async createGuest(data: GuestCreate): Promise<Guest> {
    const response = await this.client.post<Guest>('/guests', data);
    return response.data;
  }

  async updateGuest(id: number, data: GuestUpdate): Promise<Guest> {
    const response = await this.client.put<Guest>(`/guests/${id}`, data);
    return response.data;
  }

  async deleteGuest(id: number): Promise<void> {
    await this.client.delete(`/guests/${id}`);
  }

  // =========================
  // Reservation API
  // =========================

  async getReservations(propertyId?: number, limit?: number): Promise<{ reservations: Reservation[] }> {
    const response = await this.client.get('/reservations', { params: { property_id: propertyId, limit } });
    const data = response.data;
    return Array.isArray(data) ? { reservations: data } : data;
  }

  async getReservation(id: number): Promise<Reservation> {
    const response = await this.client.get<Reservation>(`/reservations/${id}`);
    return response.data;
  }

  async createReservation(data: ReservationCreate): Promise<Reservation> {
    const response = await this.client.post<Reservation>('/reservations', data);
    return response.data;
  }

  async updateReservation(id: number, data: ReservationUpdate): Promise<Reservation> {
    const response = await this.client.put<Reservation>(`/reservations/${id}`, data);
    return response.data;
  }

  async getReservationByConfirmation(confirmationNumber: string): Promise<Reservation> {
    const response = await this.client.get<Reservation>(`/reservations/confirmation/${confirmationNumber}`);
    return response.data;
  }

  async searchReservations(params?: any): Promise<Reservation[]> {
    const response = await this.client.get<Reservation[]>('/reservations', { params });
    return response.data;
  }

  async cancelReservation(id: number, reason?: string, force?: boolean): Promise<{ success: boolean }> {
    const response = await this.client.post(`/reservations/${id}/cancel`, null, { params: { reason, force } });
    return response.data;
  }

  async deleteReservation(id: number): Promise<void> {
    await this.client.delete(`/reservations/${id}`);
  }

  async confirmReservation(id: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/reservations/${id}/confirm`);
    return response.data;
  }

  async sendReservationConfirmation(reservationId: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/reservations/${reservationId}/send-confirmation`);
    return response.data;
  }

  async sendCheckInReminder(reservationId: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/reservations/${reservationId}/send-reminder`);
    return response.data;
  }

  async checkIn(id: number, data?: CheckInRequest): Promise<CheckInResponse> {
    const requestData = data || { reservation_id: id };
    const response = await this.client.post<CheckInResponse>('/operations/check-in', requestData);
    return response.data;
  }

  async checkOut(id: number, data: CheckOutRequest): Promise<Reservation> {
    const requestData = { reservation_id: id, ...data };
    const response = await this.client.post<Reservation>('/operations/check-out', requestData);
    return response.data;
  }

  async previewCheckOut(id: number): Promise<any> {
    const response = await this.client.post('/operations/check-out/preview', { reservation_id: id });
    return response.data;
  }

  // =========================
  // Dashboard & Operations API
  // =========================

  async getDashboardStats(propertyId?: number): Promise<DashboardStats> {
    const response = await this.client.get<DashboardStats>('/cached/dashboard/stats', { params: { property_id: propertyId } });
    return response.data;
  }

  async getHousekeepingTasks(propertyId?: number, date?: string): Promise<{ tasks: HousekeepingTask[] }> {
    const response = await this.client.get('/housekeeping/tasks', { params: { property_id: propertyId, target_date: date } });
    return response.data;
  }

  async getHousekeepingStatus(propertyId: number): Promise<any> {
    const response = await this.client.get(`/rooms/housekeeping/status/${propertyId}`);
    return response.data;
  }

  async startTask(taskId: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/housekeeping/tasks/${taskId}/start`);
    return response.data;
  }

  async completeTask(taskId: number, notes?: string): Promise<{ success: boolean }> {
    const response = await this.client.post(`/housekeeping/tasks/${taskId}/complete`, null, { params: { notes } });
    return response.data;
  }

  async inspectTask(taskId: number, passed: boolean, inspectorId: number, notes?: string): Promise<{ success: boolean }> {
    const response = await this.client.post(`/housekeeping/tasks/${taskId}/inspect`, null, {
      params: {
        passed,
        inspector_user_id: inspectorId,
        notes
      }
    });
    return response.data;
  }

  async getMaintenanceRequests(propertyId?: number): Promise<{ requests: MaintenanceRequest[] }> {
    const response = await this.client.get('/housekeeping/maintenance', { params: { property_id: propertyId } });
    return response.data;
  }

  async createMaintenanceRequest(data: any): Promise<any> {
    const response = await this.client.post('/housekeeping/maintenance', data);
    return response.data;
  }

  async startMaintenanceRequest(requestId: number): Promise<any> {
    const response = await this.client.post(`/housekeeping/maintenance/${requestId}/start`);
    return response.data;
  }

  async completeMaintenanceRequest(requestId: number, notes: string = 'Status updated'): Promise<any> {
    const response = await this.client.post(`/housekeeping/maintenance/${requestId}/complete`, {
      resolution_notes: notes,
      actual_cost: null
    });
    return response.data;
  }

  async closeMaintenanceRequest(requestId: number): Promise<any> {
    const response = await this.client.post(`/housekeeping/maintenance/${requestId}/close`);
    return response.data;
  }

  async autoAssignTasks(propertyId: number, date?: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/housekeeping/tasks/auto-assign', null, { params: { property_id: propertyId, target_date: date } });
    return response.data;
  }

  async getHousekeepingStaff(propertyId: number): Promise<any[]> {
    const response = await this.client.get('/housekeeping/staff', { params: { property_id: propertyId } });
    return response.data;
  }

  async deactivateHousekeepingStaff(staffId: number): Promise<any> {
    const response = await this.client.post(`/housekeeping/staff/${staffId}/deactivate`);
    return response.data;
  }

  // =========================
  // Room API
  // =========================

  async getRoom(id: number): Promise<Room> {
    const response = await this.client.get<Room>(`/rooms/${id}`);
    return response.data;
  }

  async getRooms(skip: number = 0, limit: number = 100): Promise<Room[]> {
    const response = await this.client.get<Room[]>('/rooms/', { params: { skip, limit } });
    return response.data;
  }

  async getAvailableRooms(params: any): Promise<Room[]> {
    const response = await this.client.get<Room[]>('/rooms/available', { params });
    return response.data;
  }

  async getRoomAvailability(startDate: string, endDate: string): Promise<any[]> {
    const response = await this.client.get('/rooms/availability', { params: { start_date: startDate, end_date: endDate } });
    return response.data;
  }

  async markRoomClean(id: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/rooms/${id}/clean`);
    return response.data;
  }

  async markRoomDirty(id: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/rooms/${id}/dirty`);
    return response.data;
  }

  async deleteRoom(id: number): Promise<void> {
    await this.client.delete(`/rooms/${id}`);
  }

  async createRoom(data: { property_id: number; room_type_id: number; room_number: string; floor?: number }): Promise<Room> {
    const response = await this.client.post<Room>('/rooms/', data);
    return response.data;
  }

  async getRoomTypes(propertyId?: number): Promise<any[]> {
    const response = await this.client.get('/room-types/', { params: propertyId ? { property_id: propertyId } : {} });
    return response.data;
  }

  // =========================
  // Stay & Operations API
  // =========================

  async getActiveStays(params?: any): Promise<Stay[]> {
    const response = await this.client.get<Stay[]>('/stays', { params });
    return response.data;
  }

  async addCharge(stayId: number, data: ChargeCreate): Promise<any> {
    const response = await this.client.post(`/stays/${stayId}/charges`, data);
    return response.data;
  }

  async markNoShow(reservationId: number, reason?: string, waiveFee?: boolean): Promise<{ success: boolean }> {
    const response = await this.client.post(`/operations/reservations/${reservationId}/no-show`, null, {
      params: { reason, waive_fee: waiveFee }
    });
    return response.data;
  }

  async runNightAudit(propertyId: number, date?: string): Promise<any> {
    const response = await this.client.post('/operations/night-audit', null, {
      params: {
        property_id: propertyId,
        audit_date: date
      }
    });
    return response.data;
  }

  async getWaitlist(propertyId: number): Promise<any[]> {
    const response = await this.client.get('/operations/waitlist', { params: { property_id: propertyId } });
    return Array.isArray(response.data) ? response.data : [];
  }

  async addToWaitlist(params: {
    property_id: number; guest_id: number; room_type_id: number;
    check_in_date: string; check_out_date: string; num_adults: number; priority?: number;
  }): Promise<any> {
    const response = await this.client.post('/operations/waitlist', null, { params });
    return response.data;
  }

  async promoteFromWaitlist(id: number): Promise<any> {
    const response = await this.client.post(`/operations/waitlist/${id}/promote`);
    return response.data;
  }

  async removeFromWaitlist(id: number): Promise<void> {
    await this.client.delete(`/operations/waitlist/${id}`);
  }

  async changeRoom(stayId: number, newRoomId: number, reason?: string, changeFee?: boolean): Promise<{ success: boolean }> {
    const response = await this.client.post(`/operations/stays/${stayId}/change-room`, {
      room_id: newRoomId,
      reason,
      charge_fee: changeFee
    });
    return response.data;
  }

  async getDailySummary(propertyId: number, date: string): Promise<DailySummary> {
    const response = await this.client.get(`/operations/daily-summary/${propertyId}`, { params: { date } });
    return response.data;
  }

  async runDailyHousekeeping(propertyId: number, date?: string): Promise<{ success: boolean; total: number }> {
    const response = await this.client.post(`/operations/daily-housekeeping/${propertyId}`, null, { params: { date } });
    return response.data;
  }

  // =========================
  // Guest API (extended)
  // =========================

  async searchGuests(params?: any): Promise<Guest[]> {
    const response = await this.client.get<Guest[]>('/guests', { params });
    return response.data;
  }

  // =========================
  // Analytics API
  // =========================

  async getKPISummary(propertyId?: number, date?: string): Promise<KPISummary> {
    const response = await this.client.get('/analytics/kpi-summary', { params: { property_id: propertyId, date } });
    return response.data;
  }

  async getPerformanceScorecard(propertyId?: number, date?: string): Promise<PerformanceScorecard> {
    const response = await this.client.get('/analytics/performance/scorecard', { params: { property_id: propertyId, date } });
    return response.data;
  }

  async getEfficiencyMetrics(propertyId?: number, startDate?: string, endDate?: string): Promise<EfficiencyMetrics> {
    const response = await this.client.get('/analytics/performance/efficiency', {
      params: {
        property_id: propertyId,
        start_date: startDate,
        end_date: endDate
      }
    });
    return response.data;
  }

  async getAnalyticsRevenue(propertyId: number, startDate: string, endDate: string): Promise<any[]> {
    const response = await this.client.get('/analytics/revenue', {
      params: { property_id: propertyId, start_date: startDate, end_date: endDate },
    });
    return response.data;
  }

  // =========================
  // Rate & Discount API
  // =========================

  async getRateCalendar(propertyId: number, roomTypeId: number, startDate: string, numDays: number = 30): Promise<any> {
    const response = await this.client.get('/rates/calendar', { 
      params: { 
        property_id: propertyId, 
        room_type_id: roomTypeId,
        start_date: startDate, 
        num_days: numDays 
      } 
    });
    return response.data;
  }

  async getDiscountCodes(propertyId: number, activeOnly: boolean = true): Promise<{ discount_codes: DiscountCode[] }> {
    const response = await this.client.get('/rates/discounts', {
      params: { property_id: propertyId, active_only: activeOnly }
    });
    return response.data;
  }

  async createDiscountCode(data: any): Promise<DiscountCode> {
    const response = await this.client.post('/rates/discounts', data);
    return response.data;
  }

  async updateDiscountCode(id: number, data: any): Promise<DiscountCode> {
    const response = await this.client.patch(`/rates/discounts/${id}`, data);
    return response.data;
  }

  async deleteDiscountCode(id: number): Promise<void> {
    await this.client.delete(`/rates/discounts/${id}`);
  }

  async getRatePlans(propertyId?: number): Promise<any[]> {
    const response = await this.client.get('/rates/plans', { params: { property_id: propertyId } });
    return response.data?.rate_plans ?? [];
  }

  async createRatePlan(data: any): Promise<any> {
    const response = await this.client.post('/rates/plans', data);
    return response.data;
  }

  async updateRatePlan(id: number, data: any): Promise<any> {
    const response = await this.client.patch(`/rates/plans/${id}`, data);
    return response.data;
  }

  async deleteRatePlan(id: number): Promise<void> {
    await this.client.delete(`/rates/plans/${id}`);
  }

  // =========================
  // Auth & User API
  // =========================

  async login(username: string, password: string): Promise<LoginApiResponse> {
    const response = await this.client.post<LoginApiResponse>('/auth/login', { username, password });
    return response.data;
  }

  async selectTenant(tenantId: number): Promise<{ access_token: string; refresh_token: string; tenant_id: number }> {
    const response = await this.client.post('/auth/select-tenant', { tenant_id: tenantId });
    return response.data;
  }

  async getMemberships(): Promise<{ memberships: TenantMembership[] }> {
    const response = await this.client.get('/auth/memberships');
    return response.data;
  }

  async getProperties(): Promise<Array<{ id: number; name: string; code?: string | null }>> {
    const response = await this.client.get('/properties/');
    return response.data;
  }

  async getMe(): Promise<User> {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  async logout(refreshToken?: string): Promise<{ success: boolean }> {
    const response = await this.client.post('/auth/logout', { refresh_token: refreshToken });
    return response.data;
  }

  async changePassword(oldPassword?: string, newPassword?: string): Promise<{ success: boolean }> {
    const response = await this.client.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    });
    return response.data;
  }

  async getUserList(propertyId?: number, query?: string): Promise<{ users: User[] }> {
    const response = await this.client.get('/users', {
      params: { property_id: propertyId, search: query }
    });
    return response.data;
  }

  async getUserById(id: number): Promise<User> {
    const response = await this.client.get(`/users/${id}`);
    return response.data;
  }

  async getUserStats(userId: number): Promise<UserStats> {
    const response = await this.client.get(`/users/${userId}/stats`);
    return response.data;
  }

  async getUserActivity(userId: number, limit: number = 10): Promise<{ activities: UserActivity[] }> {
    const response = await this.client.get(`/users/${userId}/activity`, {
      params: { limit }
    });
    return response.data;
  }

  async getRoleStats(): Promise<any> {
    const response = await this.client.get('/users/stats/roles');
    return response.data;
  }

  async deactivateUser(id: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/users/${id}/deactivate`);
    return response.data;
  }

  async activateUser(id: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/users/${id}/activate`);
    return response.data;
  }

  async unlockUserAccount(id: number): Promise<{ success: boolean }> {
    const response = await this.client.post(`/users/${id}/unlock`);
    return response.data;
  }

  async deleteUser(id: number): Promise<{ success: boolean }> {
    const response = await this.client.delete(`/users/${id}`);
    return response.data;
  }

  // =========================
  // Audit & Compliance API
  // =========================

  async searchAuditLogs(propertyId: number, query: string, filters?: any): Promise<{ logs: AuditLog[]; total: number }> {
    const response = await this.client.get(`/system/audit/search/${propertyId}`, {
      params: { query, ...filters }
    });
    return response.data;
  }

  async exportAuditLogs(propertyId: number, filters?: any): Promise<Blob> {
    const response = await this.client.get(`/system/audit/export/${propertyId}`, {
      params: filters,
      responseType: 'blob'
    });
    return response.data;
  }

  async getComplianceReport(propertyId: number): Promise<ComplianceReport> {
    const response = await this.client.get(`/system/compliance/report/${propertyId}`);
    return response.data;
  }

  async getSecuritySummary(): Promise<SecuritySummary> {
    const response = await this.client.get('/system/security-summary');
    return response.data;
  }

  async getRetentionStatus(): Promise<RetentionStatus> {
    const response = await this.client.get('/system/retention-status');
    return response.data;
  }

  async getAuditStats(propertyId: number): Promise<AuditStats> {
    const response = await this.client.get(`/system/audit/stats/${propertyId}`);
    return response.data;
  }

  // =========================
  // Search API
  // =========================

  async globalSearch(query: string, entities?: string[], limit: number = 20): Promise<any> {
    const response = await this.client.get('/search/global', {
      params: { q: query, entities: entities?.join(','), limit }
    });
    return response.data;
  }

  async getSearchSuggestions(query: string, context: string = 'global'): Promise<{ suggestions: string[] }> {
    const response = await this.client.get('/search/suggestions', {
      params: { query, context }
    });
    return response.data;
  }

  async getSavedSearches(): Promise<{ searches: SavedSearch[] }> {
    const response = await this.client.get('/search/saved');
    return response.data;
  }

  async getSearchHistory(context: string = 'global', limit: number = 10): Promise<{ history: any[] }> {
    const response = await this.client.get('/search/history', {
      params: { context, limit }
    });
    return response.data;
  }

  async useSavedSearch(id: number): Promise<any> {
    const response = await this.client.get(`/search/saved/${id}`);
    return response.data;
  }

  // =========================
  // System API
  // =========================

  async getDatabaseInfo(): Promise<DatabaseInfo> {
    const response = await this.client.get<DatabaseInfo>('/system/database-info');
    return response.data;
  }

  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/system/health');
    return response.data;
  }

  async getMonitoringMetrics(): Promise<MonitoringMetrics> {
    const response = await this.client.get('/system/monitoring/metrics');
    return response.data;
  }

  async clearCache(namespace: string = 'all'): Promise<{ success: boolean }> {
    const response = await this.client.post(`/system/monitoring/cache/clear/${namespace}`);
    return response.data;
  }

  // =========================
  // Notifications API
  // =========================

  async getNotificationHistory(userId?: number, limit?: number, type?: string): Promise<{ notifications: any[] }> {
    const response = await this.client.get('/notifications/history', { 
      params: { user_id: userId, limit, type } 
    });
    return response.data;
  }

  // =========================
  // Social Platform API
  // =========================

  async getPosts(params?: { institution_id?: number; type?: string; search?: string; skip?: number; limit?: number }): Promise<any[]> {
    const response = await this.client.get<any[]>('/posts', { params });
    return response.data;
  }

  async getPost(id: number): Promise<any> {
    const response = await this.client.get<any>(`/posts/${id}`);
    return response.data;
  }

  async createPost(data: { title: string; content?: string; type?: string; media_url?: string; is_pinned?: boolean; hashtags?: string }): Promise<any> {
    const response = await this.client.post<any>('/posts', data);
    return response.data;
  }

  async updatePost(id: number, data: any): Promise<any> {
    const response = await this.client.put<any>(`/posts/${id}`, data);
    return response.data;
  }

  async deletePost(id: number): Promise<void> {
    await this.client.delete(`/posts/${id}`);
  }

  async getInstitutions(): Promise<any[]> {
    const response = await this.client.get<any[]>('/institutions');
    return response.data;
  }

  async getInstitution(id: number): Promise<any> {
    const response = await this.client.get<any>(`/institutions/${id}`);
    return response.data;
  }

  async updateInstitution(id: number, data: any): Promise<any> {
    const response = await this.client.put<any>(`/institutions/${id}`, data);
    return response.data;
  }

  async uploadMedia(file: File): Promise<{ url: string; filename: string; size: number; content_type: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post('/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  }

  async getAdminAnalytics(): Promise<any> {
    const response = await this.client.get<any>('/admin/analytics');
    return response.data;
  }

  async createInstitution(data: any): Promise<any> {
    const response = await this.client.post<any>('/admin/institutions', data);
    return response.data;
  }

  async deleteInstitution(id: number): Promise<void> {
    await this.client.delete(`/admin/institutions/${id}`);
  }

  // =========================
  // Student Social Platform API
  // =========================

  async registerStudent(data: any): Promise<any> {
    const response = await this.client.post<any>('/auth/register-student', data);
    return response.data;
  }

  async verifyOtp(email: string, otpCode: string): Promise<any> {
    const response = await this.client.post<any>('/auth/verify-otp', {
      email,
      otp_code: otpCode,
    });
    return response.data;
  }

  async getStudentProfile(username: string): Promise<any> {
    const response = await this.client.get<any>(`/students/profile/${username}`);
    return response.data;
  }

  async updateStudentProfile(data: any): Promise<any> {
    const response = await this.client.put<any>('/students/profile', data);
    return response.data;
  }

  async searchSocial(q: string): Promise<any> {
    const response = await this.client.get<any>('/students/search', { params: { q } });
    return response.data;
  }

  async followUser(userId: number): Promise<any> {
    const response = await this.client.post<any>(`/students/follow/${userId}`);
    return response.data;
  }

  async unfollowUser(userId: number): Promise<any> {
    const response = await this.client.post<any>(`/students/unfollow/${userId}`);
    return response.data;
  }

  async getFollowers(userId: number): Promise<any[]> {
    const response = await this.client.get<any[]>(`/students/followers/${userId}`);
    return response.data;
  }

  async getFollowing(userId: string | number): Promise<any[]> {
    const response = await this.client.get<any[]>(`/students/following/${userId}`);
    return response.data;
  }

  async toggleLikePost(postId: number): Promise<any> {
    const response = await this.client.post<any>(`/posts/${postId}/like`);
    return response.data;
  }

  async commentOnPost(postId: number, content: string): Promise<any> {
    const response = await this.client.post<any>(`/posts/${postId}/comment`, { content });
    return response.data;
  }

  async getPostComments(postId: number): Promise<any[]> {
    const response = await this.client.get<any[]>(`/posts/${postId}/comments`);
    return response.data;
  }

  async getStudentFeed(skip: number = 0, limit: number = 20): Promise<any[]> {
    const response = await this.client.get<any[]>('/posts/student-feed', { params: { skip, limit } });
    return response.data;
  }

  // =========================
  // Stories & Highlights API
  // =========================

  async createStory(data: { media_url: string; type?: string }): Promise<any> {
    const response = await this.client.post<any>('/stories', data);
    return response.data;
  }

  async getActiveStories(): Promise<any[]> {
    const response = await this.client.get<any[]>('/stories/active');
    return response.data;
  }

  async createHighlight(data: { name: string; cover_url?: string; story_ids: number[] }): Promise<any> {
    const response = await this.client.post<any>('/highlights', data);
    return response.data;
  }

  async getHighlights(userId: number): Promise<any[]> {
    const response = await this.client.get<any[]>(`/highlights/${userId}`);
    return response.data;
  }

  // =========================
  // Chat / Messaging API
  // =========================

  async sendMessage(receiverId: number, content: string): Promise<any> {
    const response = await this.client.post<any>('/chat/send', { receiver_id: receiverId, content });
    return response.data;
  }

  async getChatHistory(partnerId: number): Promise<any[]> {
    const response = await this.client.get<any[]>(`/chat/history/${partnerId}`);
    return response.data;
  }

  async getConversations(): Promise<any[]> {
    const response = await this.client.get<any[]>('/chat/conversations');
    return response.data;
  }

  // =========================
  // Groups & Classrooms API
  // =========================

  async createGroup(data: { name: string; description?: string; is_classroom?: boolean; class_or_department?: string }): Promise<any> {
    const response = await this.client.post<any>('/groups', data);
    return response.data;
  }

  async getGroups(joinedOnly: boolean = true): Promise<any[]> {
    const response = await this.client.get<any[]>('/groups', { params: { joined_only: joinedOnly } });
    return response.data;
  }

  async joinGroup(groupId: number): Promise<any> {
    const response = await this.client.post<any>(`/groups/${groupId}/join`);
    return response.data;
  }

  async leaveGroup(groupId: number): Promise<any> {
    const response = await this.client.post<any>(`/groups/${groupId}/leave`);
    return response.data;
  }

  async getGroupMembers(groupId: number): Promise<any[]> {
    const response = await this.client.get<any[]>(`/groups/${groupId}/members`);
    return response.data;
  }

  async createAssignment(groupId: number, data: { title: string; description?: string; file_url?: string; due_date?: string }): Promise<any> {
    const response = await this.client.post<any>(`/groups/${groupId}/assignments`, data);
    return response.data;
  }

  async getAssignments(groupId: number): Promise<any[]> {
    const response = await this.client.get<any[]>(`/groups/${groupId}/assignments`);
    return response.data;
  }

  async createEvent(groupId: number, data: { title: string; description?: string; date: string; location?: string }): Promise<any> {
    const response = await this.client.post<any>(`/groups/${groupId}/events`, data);
    return response.data;
  }

  async getEvents(groupId: number): Promise<any[]> {
    const response = await this.client.get<any[]>(`/groups/${groupId}/events`);
    return response.data;
  }

  // =========================
  // Admin Approvals API
  // =========================

  async getPendingStudents(): Promise<any[]> {
    const response = await this.client.get<any[]>('/admin/pending-students');
    return response.data;
  }

  async approveStudent(userId: number): Promise<any> {
    const response = await this.client.post<any>(`/admin/students/${userId}/approve`);
    return response.data;
  }

  async rejectStudent(userId: number): Promise<any> {
    const response = await this.client.post<any>(`/admin/students/${userId}/reject`);
    return response.data;
  }

  async deleteStudent(userId: number): Promise<void> {
    await this.client.delete(`/admin/students/${userId}`);
  }

  async getAllStudents(): Promise<any[]> {
    const response = await this.client.get<any[]>('/admin/students');
    return response.data;
  }
}

export function getMediaUrl(url?: string | null): string {
  if (!url) return '';

  if (
    url.startsWith('http://') ||
    url.startsWith('https://') ||
    url.startsWith('data:')
  ) {
    return url;
  }

  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://assisi-ifl-web.onrender.com';

  if (url.startsWith('/')) {
    return `${baseUrl}${url}`;
  }

  return `${baseUrl}/${url}`;
}

export function isVideoMedia(type?: string | null, mediaUrl?: string | null): boolean {
  if (!mediaUrl) return false;
  const lowerUrl = mediaUrl.toLowerCase();
  
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'];
  if (imageExtensions.some(ext => lowerUrl.endsWith(ext))) {
    return false;
  }
  
  const videoExtensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv'];
  if (videoExtensions.some(ext => lowerUrl.endsWith(ext)) || lowerUrl.includes('mixkit') || lowerUrl.includes('pixabay')) {
    return true;
  }
  
  return type === 'video';
}

export const api = new ApiClient();
export default api;
