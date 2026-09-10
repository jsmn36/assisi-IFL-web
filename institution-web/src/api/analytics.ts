import axios from 'axios';
import { format } from 'date-fns';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const analyticsApi = {
  getOccupancy: async (propertyId: number, startDate: Date, endDate: Date) => {
    const response = await axios.get(`${API_BASE_URL}/analytics/occupancy`, {
      params: {
        property_id: propertyId,
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd')
      }
    });
    return response.data;
  },
  
  getRevenue: async (propertyId: number, startDate: Date, endDate: Date, granularity: 'daily' | 'weekly' | 'monthly' = 'daily') => {
    const response = await axios.get(`${API_BASE_URL}/analytics/revenue`, {
      params: {
        property_id: propertyId,
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd'),
        granularity
      }
    });
    return response.data;
  },
  
  getKPIs: async (propertyId: number, startDate: Date, endDate: Date) => {
    const response = await axios.get(`${API_BASE_URL}/analytics/kpis`, {
      params: {
        property_id: propertyId,
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd')
      }
    });
    return response.data;
  },

  getChannels: async (propertyId: number, startDate: Date, endDate: Date) => {
    const response = await axios.get(`${API_BASE_URL}/analytics/channels`, {
      params: {
        property_id: propertyId,
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd')
      }
    });
    return response.data;
  },

  getBookingPatterns: async (propertyId: number, lookbackDays: number = 90) => {
    const response = await axios.get(`${API_BASE_URL}/analytics/bookings/patterns`, {
      params: {
        property_id: propertyId,
        lookback_days: lookbackDays
      }
    });
    return response.data;
  }
};
