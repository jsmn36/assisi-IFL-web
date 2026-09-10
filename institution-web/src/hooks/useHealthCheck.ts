// @ts-nocheck
/**
 * useHealthCheck Hook
 * Checks backend API health status
 */
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { HealthCheckResponse } from '../types/api';

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health-check'],
    queryFn: async () => {
      const data = await api.healthCheck();
      return data;
    },
    // Refresh every 30 seconds
    refetchInterval: 30000,
  });
}
