import { useMemo } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Badge from '../../../shared/components/Badge';
import Skeleton from '../../../shared/components/Skeleton';
import { useReorderAlerts } from '../hooks/useReorderAlerts';
import type { ReorderAlert } from '../types';

type Severity = 'critical' | 'high' | 'medium' | 'low';

function classifySeverity(alert: ReorderAlert): Severity {
  if (!alert.predicted_stockout_date) return 'low';
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const stockout = new Date(alert.predicted_stockout_date + 'T00:00:00');
  const diffMs = stockout.getTime() - now.getTime();
  const daysLeft = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  if (daysLeft <= 3) return 'critical';
  if (daysLeft <= 7) return 'high';
  if (daysLeft <= 14) return 'medium';
  return 'low';
}

const severityOrder: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

function daysUntilStockout(alert: ReorderAlert): number | null {
  if (!alert.predicted_stockout_date) return null;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const stockout = new Date(alert.predicted_stockout_date + 'T00:00:00');
  return Math.ceil((stockout.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

const severityStyles: Record<Severity, { icon: string; badge: string; label: string }> = {
  critical: { icon: 'bg-red-50 text-red-600', badge: 'Out of Stock', label: 'Critical' },
  high: { icon: 'bg-orange-50 text-orange-600', badge: 'Low Stock', label: 'High' },
  medium: { icon: 'bg-yellow-50 text-yellow-600', badge: 'Low Stock', label: 'Medium' },
  low: { icon: 'bg-gray-50 text-gray-600', badge: 'Low Stock', label: 'Low' },
};

interface Props {
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export default function ReorderAlertList({ onRefresh, isRefreshing }: Props) {
  const { data: alerts, isLoading, error } = useReorderAlerts();

  const sorted = useMemo(() => {
    if (!alerts) return [];
    return [...alerts].sort((a, b) => {
      const sevA = classifySeverity(a);
      const sevB = classifySeverity(b);
      const orderDiff = severityOrder[sevA] - severityOrder[sevB];
      if (orderDiff !== 0) return orderDiff;
      const daysA = daysUntilStockout(a);
      const daysB = daysUntilStockout(b);
      if (daysA !== null && daysB !== null) return daysA - daysB;
      if (daysA !== null) return -1;
      if (daysB !== null) return 1;
      return 0;
    });
  }, [alerts]);

  return (
    <Card
      title="Reorder Alerts"
      action={
        onRefresh ? (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-1.5 rounded-md text-ink-muted hover:text-ink hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Refresh alerts"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        ) : undefined
      }
    >
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton lines={4} />
        </div>
      ) : error ? (
        <p className="text-body text-red-600">Failed to load reorder alerts.</p>
      ) : !sorted || sorted.length === 0 ? (
        <p className="text-body text-ink-muted py-4">All stock levels are healthy.</p>
      ) : (
        <div className="space-y-3">
          {sorted.map((item) => {
            const severity = classifySeverity(item);
            const styles = severityStyles[severity];
            const daysLeft = daysUntilStockout(item);
            return (
              <div key={item.sku_code} className="flex items-start gap-3 pb-3 border-b border-hairline last:border-0 last:pb-0">
                <div className={`flex items-center justify-center w-7 h-7 rounded-md shrink-0 ${styles.icon}`}>
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-body text-ink truncate">{item.product_name}</p>
                  <p className="text-mono text-caption text-ink-muted mt-0.5">{item.sku_code}</p>
                  <p className="text-caption text-ink-muted tabular-nums mt-0.5">
                    {item.quantity} units — reorder at {item.reorder_point}
                  </p>
                  {daysLeft !== null && (
                    <p className={`text-caption tabular-nums mt-0.5 ${
                      severity === 'critical' ? 'text-red-600' : 'text-ink-muted'
                    }`}>
                      ~{daysLeft} day{daysLeft !== 1 ? 's' : ''} until stockout
                    </p>
                  )}
                  {item.supplier_name && (
                    <p className="text-caption text-ink-faint mt-0.5">{item.supplier_name}</p>
                  )}
                </div>
                <Badge variant={styles.badge}>{styles.label}</Badge>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
