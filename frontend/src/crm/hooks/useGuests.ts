import { useQuery } from '@tanstack/react-query';
import { crmGuestsApi } from '../api/crmClient';
import { useCRMStore } from '../store/crmStore';

export function useGuests() {
  const { filters } = useCRMStore();

  return useQuery({
    queryKey: ['crm', 'guests', filters],
    queryFn: () => crmGuestsApi.list(filters),
    staleTime: 30_000,
  });
}
