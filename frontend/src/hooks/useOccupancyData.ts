import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';

export function useOccupancyData(propertyId: number, startDate: Date, endDate: Date) {
    return useQuery({
        queryKey: ['analytics', 'occupancy', propertyId, startDate.toISOString(), endDate.toISOString()],
        queryFn: () => analyticsApi.getOccupancy(propertyId, startDate, endDate),
        staleTime: 5 * 60 * 1000, // 5 minutes fresh matching ETL
    });
}
