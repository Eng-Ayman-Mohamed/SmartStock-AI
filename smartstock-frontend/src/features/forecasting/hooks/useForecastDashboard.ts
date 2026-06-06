import { useQuery } from '@tanstack/react-query';
import api from '../../../lib/axios';

export interface ForecastDay {
  date: string;
  demand: number;
}

export interface ForecastSKU {
  id: string;
  name: string;
  threshold: number;
  current_stock: number;
  supplier: string;
  lead_time_days: number;
  days: ForecastDay[];
}

interface ForecastDashboardResponse {
  skus: ForecastSKU[];
}

async function fetchForecastDashboard(): Promise<ForecastDashboardResponse> {
  const { data } = await api.get<ForecastDashboardResponse>('/forecasting/dashboard/');
  return data;
}

export function useForecastDashboard() {
  return useQuery({
    queryKey: ['forecast-dashboard'],
    queryFn: fetchForecastDashboard,
    staleTime: 5 * 60 * 1000,  // 5 min — forecasts don't change by the second
    retry: 2,
  });
}