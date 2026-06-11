import { useState } from 'react';
import { Check, X, Pencil, AlertTriangle, Loader2, CheckCircle, XCircle } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import { useApprovePO, useRejectPO } from '../hooks/usePurchasing';
import type { PendingPO } from '../types';

interface POApprovalCardProps {
  po: PendingPO;
  onApproved?: () => void;
  onRejected?: () => void;
}

export default function POApprovalCard({ po, onApproved, onRejected }: POApprovalCardProps) {
  const [editableQty, setEditableQty] = useState(po.recommended_qty);
  const [pendingConfirm, setPendingConfirm] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const approveMutation = useApprovePO();
  const rejectMutation = useRejectPO();

  const isLoading = approveMutation.isPending || rejectMutation.isPending;
  const isApproved = approveMutation.isSuccess;
  const isRejected = rejectMutation.isSuccess;
  const isSettled = isApproved || isRejected;

  const computedTotal = `$${(editableQty * po.unit_cost).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const handleApprove = async () => {
    if (isLoading) return;

    if (!pendingConfirm) {
      setPendingConfirm(true);
      return;
    }

    setLocalError(null);
    try {
      await approveMutation.mutateAsync({ id: po.id, qty: editableQty });
      setPendingConfirm(false);
      onApproved?.();
    } catch {
      setLocalError('Failed to submit. Please try again.');
      setPendingConfirm(false);
    }
  };

  const handleReject = async () => {
    if (isLoading) return;

    setPendingConfirm(false);
    setLocalError(null);
    try {
      await rejectMutation.mutateAsync({ id: po.id });
      onRejected?.();
    } catch {
      setLocalError('Failed to submit. Please try again.');
    }
  };

  const handleEditQty = () => {
    setEditableQty(po.recommended_qty);
    setPendingConfirm(false);
  };

  return (
    <div
      role="region"
      aria-label={`Purchase order ${po.id}`}
      className="bg-canvas border-l-[3px] border-l-amber-600 rounded-lg shadow-elevated overflow-hidden"
    >
      {/* Header */}
      <div className="px-6 pt-6 pb-4 border-b border-hairline">
        <div className="flex items-center justify-between">
          <h3 className="text-card-title text-ink">Purchase Order Draft</h3>
          <Badge variant="AI Generated" />
        </div>
      </div>

      {/* Error banner */}
      {localError && (
        <div className="mx-6 mt-4 bg-red-50 text-red-800 text-caption p-3 rounded-md">
          {localError}
        </div>
      )}

      {/* Body — success or normal */}
      {isSettled ? (
        <div className="px-6 py-8 flex items-center gap-3">
          {isApproved ? (
            <>
              <CheckCircle className="w-6 h-6 text-green-600" />
              <span className="text-body font-medium text-green-600">Purchase order approved!</span>
            </>
          ) : (
            <>
              <XCircle className="w-6 h-6 text-red-600" />
              <span className="text-body font-medium text-red-600">Purchase order rejected!</span>
            </>
          )}
        </div>
      ) : (
        <div className="px-6 pt-4 pb-2 space-y-3">
          {/* 2×2 grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-caption text-ink-muted">SKU</p>
              <p className="text-mono text-ink mt-0.5">{po.sku}</p>
            </div>
            <div>
              <p className="text-caption text-ink-muted">Supplier</p>
              <p className="text-body text-ink mt-0.5">{po.supplier}</p>
            </div>
            <div>
              <p className="text-caption text-ink-muted flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 text-red-600" /> Predicted stockout
              </p>
              <p className="text-body text-red-600 mt-0.5 tabular-nums">{po.predicted_stockout}</p>
            </div>
            <div>
              <p className="text-caption text-ink-muted">Estimated cost</p>
              <p className="text-[16px] font-medium text-ink mt-0.5 tabular-nums">{computedTotal}</p>
            </div>
          </div>

          {/* Quantity row */}
          <div className="flex items-center gap-2 pt-2">
            <p className="text-caption text-ink-muted">Recommended qty:</p>
            <input
              type="number"
              value={editableQty}
              onChange={(e) => setEditableQty(Math.max(0, parseInt(e.target.value) || 0))}
              aria-label="Purchase order quantity"
              className="w-20 h-8 px-2 rounded-md border border-hairline bg-canvas text-body text-ink tabular-nums hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
            />
          </div>

          {/* Reasoning trace (collapsible, only if agent_reasoning is not null) */}
          {po.agent_reasoning && (
            <details className="group">
              <summary className="text-caption text-ink-muted cursor-pointer hover:text-ink transition-colors">
                Why did the AI flag this?
              </summary>
              <div className="mt-2 p-3 rounded-md bg-purple-50 border-l-2 border-purple-100">
                <p className="text-caption text-ink-muted italic leading-relaxed">{po.agent_reasoning}</p>
              </div>
            </details>
          )}
        </div>
      )}

      {/* Actions bar — hidden on success */}
      {!isSettled && (
        <div className="flex items-center gap-3 px-6 pt-4 pb-6 border-t border-hairline">
          <Button
            variant="ghost"
            size="md"
            className="text-red-600 hover:bg-red-50"
            disabled={isLoading}
            onClick={handleReject}
          >
            {rejectMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <X className="w-4 h-4" />
            )}
            {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
          </Button>

          <Button
            variant="utility"
            size="md"
            disabled={isLoading}
            onClick={handleEditQty}
          >
            <Pencil className="w-4 h-4" /> Edit Qty
          </Button>

          <Button
            variant="primary"
            size="md"
            className={`flex-1 ${pendingConfirm ? 'bg-green-800 hover:bg-green-900' : 'bg-green-600 hover:bg-green-800'} text-white`}
            disabled={isLoading}
            aria-disabled={isLoading}
            onClick={handleApprove}
          >
            {approveMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Check className="w-4 h-4" />
            )}
            {approveMutation.isPending ? 'Approving...' : pendingConfirm ? 'Confirm approve?' : 'Approve'}
          </Button>
        </div>
      )}
    </div>
  );
}
