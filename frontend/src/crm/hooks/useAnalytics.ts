import { useQuery } from '@tanstack/react-query';
import { crmAnalyticsApi } from '../api/crmClient';

export function useAnalyticsSummary() {
  return useQuery({ 
    queryKey: ['crm', 'analytics', 'summary'], 
    queryFn: crmAnalyticsApi.summary, 
    staleTime: 5 * 60_000 
  });
}

export function useLTVBuckets() {
  return useQuery({ 
    queryKey: ['crm', 'analytics', 'ltv'], 
    queryFn: crmAnalyticsApi.ltv, 
    staleTime: 5 * 60_000 
  });
}

export function useRetention() {
  return useQuery({ 
    queryKey: ['crm', 'analytics', 'retention'], 
    queryFn: crmAnalyticsApi.retention, 
    staleTime: 5 * 60_000 
  });
}
