import type { SkuForecast } from '../hooks/useForecastDashboard';

export interface AlertInfo {
  sku: SkuForecast;
  severity: 'critical' | 'warning';
  message: string;
}

export function classifyAlert(sku: SkuForecast): AlertInfo | null {
  if (sku.current_stock <= sku.reorder_point) {
    return {
      sku,
      severity: 'critical',
      message: `${sku.product_name} stock is at ${sku.current_stock} — below reorder point of ${sku.reorder_point}. Consider ordering soon.`,
    };
  }

  const ratio = sku.predicted_demand_30d === 0 ? 1 : sku.current_stock / sku.predicted_demand_30d;
  if (ratio < 0.5) {
    return {
      sku,
      severity: 'warning',
      message: `${sku.product_name} has only ${sku.current_stock} units, which may be insufficient for the forecasted 30-day demand of ${sku.predicted_demand_30d.toFixed(0)}.`,
    };
  }

  return null;
}
