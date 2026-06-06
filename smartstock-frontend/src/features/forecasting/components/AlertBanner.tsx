import { AlertTriangle, Info, X } from 'lucide-react';
import type { SkuForecast } from '../hooks/useForecastDashboard';

interface AlertInfo {
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

  const ratio = sku.current_stock / sku.predicted_demand_30d;
  if (ratio < 0.5) {
    return {
      sku,
      severity: 'warning',
      message: `${sku.product_name} has only ${sku.current_stock} units, which may be insufficient for the forecasted 30-day demand of ${sku.predicted_demand_30d.toFixed(0)}.`,
    };
  }

  return null;
}

interface AlertBannerProps {
  alert: AlertInfo;
  onDismiss: (id: string) => void;
}

export default function AlertBanner({ alert, onDismiss }: AlertBannerProps) {
  const isCritical = alert.severity === 'critical';

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm ${
        isCritical
          ? 'bg-red-50 border-red-200 text-red-800'
          : 'bg-amber-50 border-amber-200 text-amber-800'
      }`}
    >
      {isCritical ? (
        <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
      ) : (
        <Info className="w-5 h-5 shrink-0 mt-0.5" />
      )}
      <p className="text-sm flex-1">{alert.message}</p>
      <button
        onClick={() => onDismiss(alert.sku.id)}
        className="shrink-0 p-0.5 rounded hover:bg-gray-800/60 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
