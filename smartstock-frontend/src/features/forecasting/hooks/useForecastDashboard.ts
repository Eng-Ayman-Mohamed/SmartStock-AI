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

export interface ForecastDashboardPagination {
  total: number;
  page: number;
  perPage: number;
}

interface ForecastDashboardData {
  skus: SkuForecast[];
  alerts: SkuForecast[];
  pagination: ForecastDashboardPagination;
}

function mapSku(raw: Record<string, unknown>): SkuForecast {
  return {
    id: raw.id as string,
    sku_code: (raw.sku_code ?? raw.id) as string,
    product_name: (raw.product_name ?? raw.name) as string,
    current_stock: (raw.current_stock ?? 0) as number,
    reorder_point: (raw.reorder_point ?? raw.threshold ?? 0) as number,
    stockout_risk: (raw.stockout_risk ?? false) as boolean,
    forecast: ((raw.days ?? raw.forecast ?? []) as ForecastDay[]).map(
      (d: ForecastDay) => ({
        date: d.date,
        demand: d.demand,
        upper_bound: d.upper_bound ?? null,
        lower_bound: d.lower_bound ?? null,
      })
    ),
    predicted_demand_30d: (raw.days as ForecastDay[] | undefined)
      ?.reduce((sum: number, d: ForecastDay) => sum + d.demand, 0) ?? 0,
    confidence_score: (raw.confidence_score as number) ?? 85,
  };
}

export function useForecastDashboard(page: number = 1, pageSize: number = 6) {
  const token = useAuthStore((s) => s.token);
  return useQuery<ForecastDashboardData>({
    queryKey: ['forecast-dashboard', page, pageSize],
    queryFn: async () => {
      const { data } = await api.get('/forecasting/dashboard/', {
        params: { page, page_size: pageSize },
      });
      const raw = data.data ?? data;
      return {
        skus: (raw.skus ?? raw ?? []).map(mapSku),
        alerts: (raw.alerts ?? []).map(mapSku),
        pagination: {
          total: (raw.total as number) ?? (raw.skus ?? raw ?? []).length,
          page: (raw.page as number) ?? page,
          perPage: (raw.per_page as number) ?? pageSize,
        },
      };
    },
    enabled: !!token,
    retry: false,
    refetchOnWindowFocus: false,
  });
}
