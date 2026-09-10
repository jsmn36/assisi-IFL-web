import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';

export function useKPIData(propertyId: number, startDate: Date, endDate: Date) {
    return useQuery({
        queryKey: ['analytics', 'kpis', propertyId, startDate.toISOString(), endDate.toISOString()],
        queryFn: () => analyticsApi.getKPIs(propertyId, startDate, endDate),
        staleTime: 5 * 60 * 1000,
    });
}
