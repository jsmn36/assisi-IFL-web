/**
 * Search analytics client.
 */
import client from '@/lib/axiosClient';

const BASE = '/api/v1/search/analytics';

export interface SearchAnalyticsSummary {
  since_days: number;
  total_searches: number;
  zero_result_searches: number;
  zero_result_rate: number;
  unique_users: number;
  unique_terms: number;
}

export interface TopQuery {
  search_term: string;
  entity_type: string;
  hits: number;
  avg_results: number;
}

export interface ZeroResultQuery {
  search_term: string;
  entity_type: string;
  hits: number;
  last_seen: string | null;
}

export interface UserPattern {
  user_id: number;
  username: string | null;
  total_searches: number;
  zero_result_searches: number;
  zero_result_rate: number;
  top_entity: string | null;
}

export const getSearchSummary = (sinceDays = 30) =>
  client.get(`${BASE}/summary`, { params: { since_days: sinceDays } }).then(r => r.data as SearchAnalyticsSummary);

export const getTopQueries = (sinceDays = 30, limit = 20, entityType?: string) =>
  client.get(`${BASE}/top-queries`, { params: { since_days: sinceDays, limit, entity_type: entityType } })
    .then(r => r.data.queries as TopQuery[]);

export const getZeroResultQueries = (sinceDays = 30, limit = 50, minHits = 2) =>
  client.get(`${BASE}/zero-result`, { params: { since_days: sinceDays, limit, min_hits: minHits } })
    .then(r => r.data.queries as ZeroResultQuery[]);

export const getSearchVolumeByHour = (sinceDays = 7) =>
  client.get(`${BASE}/volume-by-hour`, { params: { since_days: sinceDays } })
    .then(r => r.data.buckets as Array<{ hour: number; hits: number }>);

export const getUserSearchPatterns = (sinceDays = 30, limit = 20) =>
  client.get(`${BASE}/user-patterns`, { params: { since_days: sinceDays, limit } })
    .then(r => r.data.users as UserPattern[]);

export const getSavedFilterUsage = (sinceDays = 30, limit = 10) =>
  client.get(`${BASE}/saved-filter-usage`, { params: { since_days: sinceDays, limit } })
    .then(r => r.data.filters);
