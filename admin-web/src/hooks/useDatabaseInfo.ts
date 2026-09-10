// @ts-nocheck
/**
 * useDatabaseInfo Hook
 * Gets database configuration info
 */
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { DatabaseInfo } from '../types/api';

export function useDatabaseInfo() {
  return useQuery({
    queryKey: ['database-info'],
    queryFn: async () => {
      const data = await api.getDatabaseInfo();
      return data;
    },
  });
}
