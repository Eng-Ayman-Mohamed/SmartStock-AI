import { useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import Modal from "../../../shared/components/Modal";
import Button from "../../../shared/components/Button";
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

export default function AddEditProductModal({
  open,
  product,
  onClose,
  onSave,
  isPending,
}: AddEditProductModalProps) {
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formReorder, setFormReorder] = useState(10);
  const [formSafety, setFormSafety] = useState(10);

  useEffect(() => {
    if (product === "new") {
      setFormName("");
      setFormDescription("");
      setFormReorder(10);
      setFormSafety(10);
    } else if (product) {
      setFormName(product.name);
      setFormDescription(product.description);
      setFormReorder(product.reorder_point);
      setFormSafety(product.safety_stock);
    }
  }, [product]);

  const isEditing = product !== null && product !== "new";

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
                name: formName,
                description: formDescription,
                reorder_point: formReorder,
                safety_stock: formSafety,
              })
            }
            disabled={!formName.trim() || isPending}
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
          <input
            type="text"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
            className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
            placeholder="Wireless Mouse"
            aria-label="Product name"
          />
        </div>
        <div>
          <label className="block text-caption text-ink-muted mb-1">
            Description
          </label>
          <input
            type="text"
            value={formDescription}
            onChange={(e) => setFormDescription(e.target.value)}
            className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
            placeholder="Optional description"
            aria-label="Product description"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-caption text-ink-muted mb-1">
              Reorder Point
            </label>
            <input
              type="number"
              value={formReorder}
              onChange={(e) => setFormReorder(Number(e.target.value))}
              className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink tabular-nums hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
              aria-label="Reorder point"
            />
          </div>
          <div>
            <label className="block text-caption text-ink-muted mb-1">
              Safety Stock
            </label>
            <input
              type="number"
              value={formSafety}
              onChange={(e) => setFormSafety(Number(e.target.value))}
              className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink tabular-nums hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
              aria-label="Safety stock"
            />
          </div>
        </div>
      </div>
    </Modal>
  );
}
