import { ShoppingCart, Check, X } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import EmptyState from '../../../shared/components/EmptyState';
import Skeleton from '../../../shared/components/Skeleton';
import { useApprovePO, usePendingPOs, useRejectPO } from '../hooks/usePendingPOs';
import { useToastStore } from '../../../store/toastStore';
import { formatCurrency } from '../../../shared/utils/formatters';
import type { PurchaseOrder } from '../types';

function PendingPOItem({ po, onApprove, onReject, isMutating }: {
  po: PurchaseOrder;
  onApprove: () => void;
  onReject: () => void;
  isMutating: boolean;
}) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-md border border-hairline hover:bg-canvas-soft transition-colors">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-body font-medium text-ink truncate">{po.product_name}</span>
          <Badge>{po.status}</Badge>
        </div>
        <p className="text-caption text-ink-muted mt-0.5">
          <span className="text-mono">{po.sku_code}</span> — {po.supplier_name}
        </p>
        <p className="text-caption text-ink-muted tabular-nums mt-0.5">
          {po.quantity} units — {formatCurrency(Number(po.total_cost))}
        </p>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <Button
          variant="primary"
          size="sm"
          className="bg-green-600 hover:bg-green-800"
          onClick={onApprove}
          disabled={isMutating}
        >
          <Check className="w-3.5 h-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="text-red-600 hover:bg-red-50"
          onClick={onReject}
          disabled={isMutating}
        >
          <X className="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  );
}

export default function PendingPOQueue() {
  const { data: pos, isLoading, error } = usePendingPOs();
  const approvePO = useApprovePO();
  const rejectPO = useRejectPO();
  const addToast = useToastStore((s) => s.addToast);

  const handleApprove = (po: PurchaseOrder) => {
    approvePO.mutate(po.id, {
      onSuccess: () => addToast(`PO-${po.id} approved`, 'success'),
      onError: () => addToast(`Failed to approve PO-${po.id}`, 'error'),
    });
  };

  const handleReject = (po: PurchaseOrder) => {
    rejectPO.mutate(po.id, {
      onSuccess: () => addToast(`PO-${po.id} rejected`, 'success'),
      onError: () => addToast(`Failed to reject PO-${po.id}`, 'error'),
    });
  };

  return (
    <Card
      title="Pending Purchase Orders"
      subtitle={isLoading || error ? undefined : `${pos?.length ?? 0} orders awaiting review`}
    >
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton lines={3} />
        </div>
      ) : error ? (
        <p className="text-body text-red-600">Failed to load purchase orders.</p>
      ) : !pos || pos.length === 0 ? (
        <EmptyState
          icon={ShoppingCart}
          heading="All caught up on approvals"
          body="No purchase orders are pending approval."
        />
      ) : (
        <div className="space-y-2">
          {pos.map((po) => (
            <PendingPOItem
              key={po.id}
              po={po}
              onApprove={() => handleApprove(po)}
              onReject={() => handleReject(po)}
              isMutating={approvePO.isPending || rejectPO.isPending}
            />
          ))}
        </div>
      )}
    </Card>
  );
}
