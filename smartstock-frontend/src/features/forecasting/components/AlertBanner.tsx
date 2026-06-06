import { AlertTriangle, AlertCircle, X } from 'lucide-react';
import type { ForecastSKU } from '../hooks/useForecastDashboard';

interface Alert {
  severity: 'critical' | 'warning';
  daysUntil: number;
  sku: ForecastSKU;
}

export function classifyAlert(sku: ForecastSKU): Alert | null {
  const firstBelowIdx = sku.days.findIndex(d => d.demand < sku.threshold);
  if (firstBelowIdx === -1 && sku.current_stock >= sku.threshold) return null;
  const critical = sku.current_stock < sku.threshold ||
    sku.days.slice(0, 7).some(d => d.demand === 0);
  return { severity: critical ? 'critical' : 'warning', daysUntil: firstBelowIdx, sku };
}

interface Props { alert: Alert; onDismiss: (id: string) => void; }

export default function AlertBanner({ alert, onDismiss }: Props) {
  const { severity, daysUntil, sku } = alert;
  const isCritical = severity === 'critical';
  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border text-sm
      ${isCritical
        ? 'bg-danger/10 border-danger/30 text-danger'
        : 'bg-warning/10 border-warning/30 text-warning'}`}>
      {isCritical
        ? <AlertTriangle className="w-4 h-4 shrink-0" />
        : <AlertCircle className="w-4 h-4 shrink-0" />}
      <span className="flex-1 text-surface-200">
        <span className="font-semibold">{sku.id}</span>{' · '}{sku.name}{' — '}
        {isCritical
          ? `stock (${sku.current_stock}) is below reorder threshold (${sku.threshold})`
          : `demand dips below threshold in ${daysUntil} days`}
      </span>
      <button onClick={() => onDismiss(sku.id)} className="text-surface-500 hover:text-surface-300">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}