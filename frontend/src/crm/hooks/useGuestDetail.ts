import { useQuery } from '@tanstack/react-query';
import { crmGuestsApi } from '../api/crmClient';

export function useGuestDetail(guestId: number) {
  return useQuery({
    queryKey: ['crm', 'guest', guestId],
    queryFn: () => crmGuestsApi.get(guestId),
    staleTime: 60_000,
    enabled: guestId > 0,
  });
}
