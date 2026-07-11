import { useQuery } from '@tanstack/react-query';
import { crmSegmentsApi } from '../api/crmClient';
import type { SegmentName, GuestListFilters } from '../types/crm';

export function useSegments() {
  return useQuery({
    queryKey: ['crm', 'segments'],
    queryFn: crmSegmentsApi.list,
    staleTime: 5 * 60_000,
  });
}

export function useSegmentGuests(segmentName: SegmentName, filters: Partial<GuestListFilters> = {}) {
  return useQuery({
    queryKey: ['crm', 'segments', segmentName, 'guests', filters],
    queryFn: () => crmSegmentsApi.getGuests(segmentName, filters),
    staleTime: 60_000,
    enabled: !!segmentName,
  });
}
