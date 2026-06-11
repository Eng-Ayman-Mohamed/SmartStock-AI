import { AlertTriangle } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Badge from '../../../shared/components/Badge';
import Skeleton from '../../../shared/components/Skeleton';
import { useReorderAlerts } from '../hooks/useReorderAlerts';

export default function ReorderAlertList() {
  const { data: alerts, isLoading, error } = useReorderAlerts();

  return (
    <Card title="Reorder Alerts">
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton lines={4} />
        </div>
      ) : error ? (
        <p className="text-body text-red-600">Failed to load reorder alerts.</p>
      ) : !alerts || alerts.length === 0 ? (
        <p className="text-body text-ink-muted py-4">All stock levels are healthy.</p>
      ) : (
        <div className="space-y-3">
          {alerts.map((item) => {
            const severity = item.quantity === 0
              ? 'critical'
              : item.quantity <= Math.floor(item.reorder_point * 0.5)
                ? 'critical'
                : 'warning';
            return (
              <div key={item.sku_code} className="flex items-start gap-3 pb-3 border-b border-hairline last:border-0 last:pb-0">
                <div className={`flex items-center justify-center w-7 h-7 rounded-md shrink-0 ${
                  severity === 'critical' ? 'bg-red-50' : 'bg-orange-50'
                }`}>
                  <AlertTriangle className={`w-4 h-4 ${
                    severity === 'critical' ? 'text-red-600' : 'text-orange-600'
                  }`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-body text-ink truncate">{item.product_name}</p>
                  <p className="text-mono text-caption text-ink-muted mt-0.5">{item.sku_code}</p>
                  <p className="text-caption text-ink-muted tabular-nums mt-0.5">
                    {item.quantity} units — reorder at {item.reorder_point}
                  </p>
                  {item.supplier_name && (
                    <p className="text-caption text-ink-faint mt-0.5">{item.supplier_name}</p>
                  )}
                </div>
                <Badge variant={severity === 'critical' ? 'Out of Stock' : 'Low Stock'}>
                  {severity === 'critical' ? 'Critical' : 'Low'}
                </Badge>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
