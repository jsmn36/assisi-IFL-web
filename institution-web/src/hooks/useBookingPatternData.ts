import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';

export function useBookingPatternsData(propertyId: number, lookbackDays: number = 90) {
    return useQuery({
        queryKey: ['analytics', 'booking_patterns', propertyId, lookbackDays],
        queryFn: () => analyticsApi.getBookingPatterns(propertyId, lookbackDays),
        staleTime: 5 * 60 * 1000,
    });
}
