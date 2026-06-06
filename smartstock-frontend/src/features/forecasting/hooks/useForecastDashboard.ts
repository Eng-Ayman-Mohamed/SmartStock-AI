import { useQuery } from '@tanstack/react-query';
import api from '../../../lib/axios';

export interface SkuForecast {
  id: string;
  sku_code: string;
  product_name: string;
  current_stock: number;
  reorder_point: number;
  forecast: { date: string; predicted_demand: number }[];
  predicted_demand_30d: number;
  confidence_score: number;
}

interface ForecastDashboardData {
  skus: SkuForecast[];
}

export function useForecastDashboard() {
  return useQuery<ForecastDashboardData>({
    queryKey: ['forecast-dashboard'],
    queryFn: async () => {
      const { data } = await api.get('/forecasting/dashboard/');
      return data;
    },
    refetchOnWindowFocus: false,
    retry: 2,
  });
}
