// @ts-nocheck
/**
 * useOptimizedQuery Hook
 * React Query-like hook with caching and optimized API client integration.
 */
import { useState, useEffect, useCallback } from 'react';
import { optimizedApi } from '@/lib/optimizedApi';

interface UseOptimizedQueryOptions {
  enabled?: boolean;
  cacheTTL?: number;
  refetchOnMount?: boolean;
  refetchInterval?: number;
}

export function useOptimizedQuery<T>(
  endpoint: string,
  params?: any,
  options: UseOptimizedQueryOptions = {}
) {
  const {
    enabled = true,
    cacheTTL = 300000,
    refetchOnMount = true,
    refetchInterval,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<Error | null>(null);

  // Stringify params for useCallback dependency
  const paramString = JSON.stringify(params);

  const fetchData = useCallback(async () => {
    if (!enabled) return;

    setLoading(true);
    setError(null);

    try {
      const result = await optimizedApi.get<T>(endpoint, params, cacheTTL);
      setData(result);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [endpoint, paramString, enabled, cacheTTL]);

  useEffect(() => {
    if (refetchOnMount) {
      fetchData();
    }
  }, [fetchData, refetchOnMount]);

  // Handle refetch intervals
  useEffect(() => {
    if (refetchInterval && enabled) {
      const interval = setInterval(fetchData, refetchInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, refetchInterval, enabled]);

  const refetch = useCallback(() => {
    return fetchData();
  }, [fetchData]);

  const invalidate = useCallback(async () => {
    await optimizedApi.invalidate(endpoint, params);
    await fetchData();
  }, [endpoint, params, fetchData]);

  return {
    data,
    loading,
    error,
    refetch,
    invalidate,
  };
}
