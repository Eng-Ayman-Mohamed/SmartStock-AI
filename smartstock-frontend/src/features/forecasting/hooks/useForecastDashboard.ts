import { useQuery } from '@tanstack/react-query';
import api from '../../../lib/axios';
import { useAuthStore } from '../../../store/authStore';

export interface ForecastDay {
  date: string;
  demand: number;
  upper_bound: number | null;
  lower_bound: number | null;
}

export interface SkuForecast {
  id: string;
  sku_code: string;
  product_name: string;
  current_stock: number;
  reorder_point: number;
  stockout_risk: boolean;
  forecast: ForecastDay[];
  predicted_demand_30d: number;
  confidence_score: number;
}

interface ForecastDashboardData {
  skus: SkuForecast[];
}

export function useForecastDashboard() {
  const token = useAuthStore((s) => s.token);
  return useQuery<ForecastDashboardData>({
    queryKey: ['forecast-dashboard'],
    queryFn: async () => {
      const { data } = await api.get('/forecasting/dashboard/');
      const raw = data.data ?? data;
      return {
        skus: (raw.skus ?? raw ?? []).map((sku: Record<string, unknown>) => ({
          id: sku.id as string,
          sku_code: (sku.sku_code ?? sku.id) as string,
          product_name: (sku.product_name ?? sku.name) as string,
          current_stock: (sku.current_stock ?? 0) as number,
          reorder_point: (sku.reorder_point ?? sku.threshold ?? 0) as number,
          stockout_risk: (sku.stockout_risk ?? false) as boolean,
          forecast: ((sku.days ?? sku.forecast ?? []) as ForecastDay[]).map(
            (d: ForecastDay) => ({
              date: d.date,
              demand: d.demand,
              upper_bound: d.upper_bound ?? null,
              lower_bound: d.lower_bound ?? null,
            })
          ),
          predicted_demand_30d: (sku.days as ForecastDay[] | undefined)
            ?.reduce((sum: number, d: ForecastDay) => sum + d.demand, 0) ?? 0,
          confidence_score: 85,
        })),
      };
    },
    enabled: !!token,
    retry: false,
    refetchOnWindowFocus: false,
  });
}
