import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';

export function useRevenueData(
    propertyId: number,
    startDate: Date,
    endDate: Date,
    granularity: 'daily' | 'weekly' | 'monthly' = 'daily'
) {
    return useQuery({
        queryKey: ['analytics', 'revenue', propertyId, startDate.toISOString(), endDate.toISOString(), granularity],
        queryFn: () => analyticsApi.getRevenue(propertyId, startDate, endDate, granularity),
        staleTime: 5 * 60 * 1000,
    });
}
