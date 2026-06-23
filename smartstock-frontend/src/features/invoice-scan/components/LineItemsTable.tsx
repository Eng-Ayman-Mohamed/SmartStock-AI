import { Plus, Trash2 } from 'lucide-react';
import Button from '../../../shared/components/Button';
import { ConfidenceBadge } from '../confidence';
import type { InvoiceLineItem } from '../types';

type ColumnKey = keyof InvoiceLineItem;

const COLUMNS: { key: ColumnKey; label: string; type: 'text' | 'number'; width: string }[] = [
  { key: 'item_name', label: 'Item Name', type: 'text', width: 'min-w-[160px]' },
  { key: 'sku_code', label: 'SKU', type: 'text', width: 'min-w-[110px]' },
  { key: 'quantity', label: 'Qty', type: 'number', width: 'min-w-[80px]' },
  { key: 'unit_price', label: 'Unit Price', type: 'number', width: 'min-w-[110px]' },
  { key: 'total_price', label: 'Total', type: 'number', width: 'min-w-[110px]' },
];

const EMPTY_LINE: InvoiceLineItem = {
  item_name: '',
  sku_code: '',
  quantity: '',
  unit_price: '',
  total_price: '',
};

function toNumber(value: string | number | null | undefined): number | null {
  if (value === '' || value === null || value === undefined) return null;
  const parsed = typeof value === 'number' ? value : parseFloat(String(value));
  return Number.isFinite(parsed) ? parsed : null;
}

interface LineItemsTableProps {
  items: InvoiceLineItem[];
  lineConfidence?: number;
  onChange: (items: InvoiceLineItem[]) => void;
}

export default function LineItemsTable({ items, lineConfidence, onChange }: LineItemsTableProps) {
  function updateCell(index: number, key: ColumnKey, value: string) {
    const next = items.map((item, i) => {
      if (i !== index) return item;
      const row: InvoiceLineItem = { ...item, [key]: value };
      if (key === 'quantity' || key === 'unit_price') {
        const quantity = toNumber(key === 'quantity' ? value : row.quantity);
        const unitPrice = toNumber(key === 'unit_price' ? value : row.unit_price);
        const totalEmpty = row.total_price === '' || row.total_price === null;
        if (quantity !== null && unitPrice !== null && totalEmpty) {
          row.total_price = Number((quantity * unitPrice).toFixed(2));
        }
      }
      return row;
    });
    onChange(next);
  }

  function addRow() {
    onChange([...items, { ...EMPTY_LINE }]);
  }

  function removeRow(index: number) {
    onChange(items.filter((_, i) => i !== index));
  }

  const subtotal = items.reduce((sum, item) => {
    const total =
      toNumber(item.total_price) ?? (toNumber(item.quantity) ?? 0) * (toNumber(item.unit_price) ?? 0);
    return sum + (total || 0);
  }, 0);

  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <span className="text-caption font-medium text-ink-secondary">
          Line Items ({items.length})
        </span>
        <ConfidenceBadge value={lineConfidence} />
      </div>

      <div className="overflow-x-auto rounded-lg border border-hairline">
        <table className="w-full min-w-[580px] border-collapse text-body">
          <thead>
            <tr className="bg-canvas-soft text-left">
              {COLUMNS.map((column) => (
                <th key={column.key} className="px-3 py-2 text-caption font-medium text-ink-muted">
                  {column.label}
                </th>
              ))}
              <th className="w-10 px-2 py-2" aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={COLUMNS.length + 1} className="px-3 py-6 text-center text-caption text-ink-muted">
                  No line items detected. Add a row to enter products manually.
                </td>
              </tr>
            ) : (
              items.map((item, index) => (
                <tr key={index} className="border-t border-hairline">
                  {COLUMNS.map((column) => (
                    <td key={column.key} className="px-2 py-1.5 align-top">
                      <input
                        type={column.type}
                        step={column.type === 'number' ? '0.01' : undefined}
                        min={column.type === 'number' ? '0' : undefined}
                        value={item[column.key] == null ? '' : String(item[column.key])}
                        onChange={(event) => updateCell(index, column.key, event.target.value)}
                        aria-label={`${column.label} for line ${index + 1}`}
                        className={`h-9 w-full ${column.width} rounded-md border border-hairline bg-canvas px-2.5 text-body text-ink transition-colors hover:border-ink-muted focus:border-brand-600 focus:outline-none`}
                      />
                    </td>
                  ))}
                  <td className="px-2 py-1.5 text-center align-middle">
                    <button
                      type="button"
                      onClick={() => removeRow(index)}
                      aria-label={`Remove line ${index + 1}`}
                      className="text-ink-faint transition-colors hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" onClick={addRow}>
          <Plus className="h-4 w-4" /> Add row
        </Button>
        <span className="text-caption text-ink-muted">
          Subtotal:{' '}
          <span className="font-medium tabular-nums text-ink">{subtotal.toFixed(2)}</span>
        </span>
      </div>
    </div>
  );
}
