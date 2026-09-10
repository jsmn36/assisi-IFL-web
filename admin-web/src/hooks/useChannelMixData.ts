import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';

export function useChannelMixData(propertyId: number, startDate: Date, endDate: Date) {
    return useQuery({
        queryKey: ['analytics', 'channels', propertyId, startDate.toISOString(), endDate.toISOString()],
        queryFn: () => analyticsApi.getChannels(propertyId, startDate, endDate),
        staleTime: 5 * 60 * 1000,
    });
}
