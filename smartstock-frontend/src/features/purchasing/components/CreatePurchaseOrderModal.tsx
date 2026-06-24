import { useState } from "react";
import { Plus, X } from "lucide-react";
import Modal from "../../../shared/components/Modal";
import Button from "../../../shared/components/Button";
import type { SKUOption, SupplierOption } from "../api";

interface CreatePurchaseOrderModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: {
    sku: number;
    supplier: number;
    quantity: number;
    total_cost: number;
    notes: string;
  }) => void;
  isPending: boolean;
  skuOptions: SKUOption[];
  supplierOptions: SupplierOption[];
}

export default function CreatePurchaseOrderModal({
  open,
  onClose,
  onSave,
  isPending,
  skuOptions,
  supplierOptions,
}: CreatePurchaseOrderModalProps) {
  const [form, setForm] = useState({
    sku: 0,
    supplier: 0,
    quantity: 1,
    total_cost: 0,
    notes: "",
  });

  function update(field: string, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  const isValid = form.sku > 0 && form.supplier > 0 && form.quantity > 0 && form.total_cost > 0;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="New Purchase Order"
      footer={
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="secondary" size="md" onClick={onClose}>
            <X className="w-4 h-4" /> Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={() =>
              onSave({
                sku: form.sku,
                supplier: form.supplier,
                quantity: form.quantity,
                total_cost: form.total_cost,
                notes: form.notes,
              })
            }
            disabled={!isValid || isPending}
          >
            <Plus className="w-4 h-4" />{" "}
            {isPending ? "Creating..." : "Create Order"}
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <div>
          <label className="block text-caption text-ink-muted mb-1">
            SKU
          </label>
          <select
            value={form.sku}
            onChange={(e) => update("sku", Number(e.target.value))}
            className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
            aria-label="Select SKU"
          >
            <option value={0}>Select a SKU...</option>
            {skuOptions.map((sku) => (
              <option key={sku.id} value={sku.id}>
                {sku.code} - {sku.product_name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-caption text-ink-muted mb-1">
            Supplier
          </label>
          <select
            value={form.supplier}
            onChange={(e) => update("supplier", Number(e.target.value))}
            className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
            aria-label="Select supplier"
          >
            <option value={0}>Select a supplier...</option>
            {supplierOptions.map((supplier) => (
              <option key={supplier.id} value={supplier.id}>
                {supplier.name}
              </option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-caption text-ink-muted mb-1">
              Quantity
            </label>
            <input
              type="number"
              min={1}
              value={form.quantity}
              onChange={(e) => update("quantity", Number(e.target.value))}
              className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink tabular-nums hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
              aria-label="Quantity"
            />
          </div>
          <div>
            <label className="block text-caption text-ink-muted mb-1">
              Total Cost ($)
            </label>
            <input
              type="number"
              min={0}
              step={0.01}
              value={form.total_cost}
              onChange={(e) => update("total_cost", Number(e.target.value))}
              className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink tabular-nums hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
              aria-label="Total cost"
            />
          </div>
        </div>
        <div>
          <label className="block text-caption text-ink-muted mb-1">
            Notes (optional)
          </label>
          <textarea
            value={form.notes}
            onChange={(e) => update("notes", e.target.value)}
            className="w-full h-20 px-3 py-2 rounded-md border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors resize-none"
            placeholder="Any additional notes..."
            aria-label="Notes"
          />
        </div>
      </div>
    </Modal>
  );
}
