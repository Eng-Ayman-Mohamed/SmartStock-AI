import { useState } from "react";
import { ArrowUpDown, X } from "lucide-react";
import Modal from "../../../shared/components/Modal";
import Button from "../../../shared/components/Button";
import Input from "../../../shared/components/Input";

interface AdjustStockModalProps {
  open: boolean;
  stockInfo: { stockId: number; skuCode: string } | null;
  onClose: () => void;
  onAdjust: (data: { delta: number; reason: string }) => void;
  isPending: boolean;
}

export default function AdjustStockModal({
  open,
  stockInfo,
  onClose,
  onAdjust,
  isPending,
}: AdjustStockModalProps) {
  const [delta, setDelta] = useState("");
  const [reason, setReason] = useState("");

  function handleClose() {
    setDelta("");
    setReason("");
    onClose();
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title={`Adjust Stock — ${stockInfo?.skuCode ?? ""}`}
      footer={
        <div className="flex items-center gap-3">
          <Button variant="secondary" size="md" onClick={handleClose}>
            <X className="w-4 h-4" /> Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={() =>
              onAdjust({ delta: Number(delta), reason })
            }
            disabled={isPending || !delta}
          >
            <ArrowUpDown className="w-4 h-4" /> Adjust
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <div>
          <label className="block text-caption font-medium text-ink-secondary mb-1">
            Quantity Delta
          </label>
          <Input
            type="number"
            inputMode="decimal"
            value={delta}
            onChange={(e) => setDelta(e.target.value)}
            placeholder="e.g. 10 or -5"
            aria-label="Quantity delta"
          />
          <p className="text-caption text-ink-muted mt-1">
            Positive to add stock, negative to remove.
          </p>
        </div>
        <div>
          <label className="block text-caption font-medium text-ink-secondary mb-1">
            Reason (optional)
          </label>
          <Input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Received shipment"
            aria-label="Reason"
            autoCapitalize="sentences"
          />
        </div>
      </div>
    </Modal>
  );
}
