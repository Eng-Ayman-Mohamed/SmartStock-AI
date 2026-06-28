import { ShoppingCart, Check, X, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Card from '../../../shared/components/Card';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import EmptyState from '../../../shared/components/EmptyState';
import Skeleton from '../../../shared/components/Skeleton';
import { useApprovePO, usePendingPOs, useRejectPO } from '../hooks/usePendingPOs';
import { useAuthStore } from '../../../store/authStore';
import { useToastStore } from '../../../store/toastStore';
import { formatCurrency } from '../../../shared/utils/formatters';
import type { PurchaseOrder } from '../types';
import type { Role } from '../../../store/authStore';

const MANAGER_ROLES: Role[] = ['manager', 'admin'];

function PendingPOItem({ po, onApprove, onReject, isMutating, canAct, onClick }: {
  po: PurchaseOrder;
  onApprove: () => void;
  onReject: () => void;
  isMutating: boolean;
  canAct: boolean;
  onClick: () => void;
}) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      onClick={onClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      className="flex items-start gap-3 p-3 rounded-md border border-hairline hover:bg-canvas-soft transition-colors cursor-pointer"
    >
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2">
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
        {canAct ? (
          <>
            <Button
              variant="primary"
              size="sm"
              className="bg-green-600 hover:bg-green-800"
              onClick={(e) => { e.stopPropagation(); onApprove(); }}
              disabled={isMutating}
            >
              <Check className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30"
              onClick={(e) => { e.stopPropagation(); onReject(); }}
              disabled={isMutating}
            >
              <X className="w-3.5 h-3.5" />
            </Button>
          </>
        ) : (
          <span className="text-caption text-ink-muted flex items-center gap-1">
            <Eye className="w-3.5 h-3.5" />
            View only
          </span>
        )}
      </div>
    </div>
  );
}

export default function PendingPOQueue() {
  const navigate = useNavigate();
  const { data: pos, isLoading, error, refetch } = usePendingPOs();
  const user = useAuthStore((s) => s.user);
  const canAct = user ? MANAGER_ROLES.includes(user.role) : false;
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

  const handlePOClick = (po: PurchaseOrder) => {
    navigate(`/purchasing?po=PO-${po.id}`);
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
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-body text-red-600">{error?.message ?? 'Failed to load purchase orders.'}</p>
          <button onClick={() => refetch()} className="underline text-sm font-medium text-red-600 min-h-[44px]">Try again</button>
        </div>
      ) : !pos || pos.length === 0 ? (
        <EmptyState
          icon={ShoppingCart}
          heading="All caught up on approvals"
          body="No purchase orders are pending approval."
        />
      ) : (
        <div className="space-y-2 max-h-[360px] overflow-y-auto overscroll-contain">
          {pos.map((po) => (
            <PendingPOItem
              key={po.id}
              po={po}
              onApprove={() => handleApprove(po)}
              onReject={() => handleReject(po)}
              isMutating={approvePO.isPending || rejectPO.isPending}
              canAct={canAct}
              onClick={() => handlePOClick(po)}
            />
          ))}
        </div>
      )}
    </Card>
  );
}
