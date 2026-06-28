import { useState } from "react";
import { Plus, X } from "lucide-react";
import Modal from "../../../shared/components/Modal";
import Button from "../../../shared/components/Button";
import Input from "../../../shared/components/Input";
import type { Product } from "../hooks/useInventory";

interface AddEditProductModalProps {
  open: boolean;
  product: Product | "new" | null;
  onClose: () => void;
  onSave: (data: {
    name: string;
    description: string;
    reorder_point: number;
    safety_stock: number;
  }) => void;
  isPending: boolean;
}

function formStateFromProduct(product: Product | "new" | null) {
  if (product === "new" || !product) {
    return { name: "", description: "", reorder_point: 10, safety_stock: 10 };
  }
  return {
    name: product.name,
    description: product.description,
    reorder_point: product.reorder_point,
    safety_stock: product.safety_stock,
  };
}

export default function AddEditProductModal({
  open,
  product,
  onClose,
  onSave,
  isPending,
}: AddEditProductModalProps) {
  const [form, setForm] = useState(() => formStateFromProduct(product));
  const isEditing = product !== null && product !== "new";

  function update(field: "name" | "description", value: string): void;
  function update(field: "reorder_point" | "safety_stock", value: number): void;
  function update(field: string, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEditing ? "Edit Product" : "New Product"}
      footer={
        <div className="flex items-center gap-3">
          <Button variant="secondary" size="md" onClick={onClose}>
            <X className="w-4 h-4" /> Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={() =>
              onSave({
                name: form.name,
                description: form.description,
                reorder_point: form.reorder_point,
                safety_stock: form.safety_stock,
              })
            }
            disabled={!form.name.trim() || isPending}
          >
            <Plus className="w-4 h-4" />{" "}
            {isEditing ? "Save Changes" : "Create Product"}
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <div>
          <label className="block text-caption text-ink-muted mb-1">
            Product Name
          </label>
          <Input
            type="text"
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            placeholder="Wireless Mouse"
            aria-label="Product name"
          />
        </div>
        <div>
          <label className="block text-caption text-ink-muted mb-1">
            Description
          </label>
          <Input
            type="text"
            value={form.description}
            onChange={(e) => update("description", e.target.value)}
            placeholder="Optional description"
            aria-label="Product description"
          />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-caption text-ink-muted mb-1">
              Reorder Point
            </label>
            <Input
              type="number"
              inputMode="decimal"
              value={form.reorder_point}
              onChange={(e) => update("reorder_point", Number(e.target.value))}
              aria-label="Reorder point"
            />
          </div>
          <div>
            <label className="block text-caption text-ink-muted mb-1">
              Safety Stock
            </label>
            <Input
              type="number"
              inputMode="decimal"
              value={form.safety_stock}
              onChange={(e) => update("safety_stock", Number(e.target.value))}
              aria-label="Safety stock"
            />
          </div>
        </div>
      </div>
    </Modal>
  );
}
