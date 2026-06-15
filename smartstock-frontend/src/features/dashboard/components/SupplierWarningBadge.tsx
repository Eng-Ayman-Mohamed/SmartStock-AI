import { AlertTriangle } from 'lucide-react';
import { useOverdueSuppliers } from '../hooks/useOverdueSuppliers';

export default function SupplierWarningBadge() {
  const { data: overdue, isLoading, error } = useOverdueSuppliers();

  if (isLoading) {
    return (
      <div className="flex items-start gap-3 p-3 rounded-md border border-gray-200 bg-gray-50 animate-pulse">
        <div className="flex items-center justify-center w-7 h-7 rounded-md bg-gray-200 shrink-0">
          <AlertTriangle className="w-4 h-4 text-gray-400" />
        </div>
        <div className="flex-1 min-w-0 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-200 rounded w-1/2" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-start gap-3 p-3 rounded-md border border-gray-200 bg-gray-50" title="Could not check suppliers">
        <div className="flex items-center justify-center w-7 h-7 rounded-md bg-gray-100 shrink-0">
          <AlertTriangle className="w-4 h-4 text-gray-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-body text-gray-500 font-medium">Could not check suppliers</p>
        </div>
      </div>
    );
  }

  if (!overdue || overdue.length === 0) {
    return null;
  }

  return (
    <div className="flex items-start gap-3 p-3 rounded-md border border-orange-200 bg-orange-50">
      <div className="flex items-center justify-center w-7 h-7 rounded-md bg-orange-100 shrink-0">
        <AlertTriangle className="w-4 h-4 text-orange-600" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-body text-ink font-medium">
          {overdue.length} supplier{overdue.length > 1 ? 's' : ''} non-response
        </p>
        <p className="text-caption text-ink-muted mt-0.5">
          Supplier has not responded within the expected timeframe.
        </p>
        {overdue.map((item) => (
          <div key={item.supplier_id} className="mt-1">
            <p className="text-caption text-orange-700 tabular-nums">
              {item.supplier_name} — overdue by {item.days_overdue} day{item.days_overdue > 1 ? 's' : ''}
            </p>
            {item.overdue_pos.map((po) => (
              <p key={po.po_id} className="text-caption text-ink-muted tabular-nums ml-2">
                {po.po_number}
              </p>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
