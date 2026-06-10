import { ShoppingCart, Plus, Check, X, Pencil, AlertTriangle } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import EmptyState from '../../../shared/components/EmptyState';
import DataTable from '../../../shared/components/DataTable';
import type { Column } from '../../../shared/components/DataTable';

interface PendingPO {
  id: string;
  product: string;
  sku: string;
  qty: number;
  supplier: string;
  predictedStockout: string;
  recommendedQty: number;
  estimatedCost: string;
}

const pendingPOs: PendingPO[] = [
  {
    id: 'PO-1042', product: 'Wireless Mouse', sku: 'WM-2024-001',
    qty: 200, supplier: 'TechSupply Co.',
    predictedStockout: '15 Jun 2025', recommendedQty: 250, estimatedCost: '$5,312.50',
  },
  {
    id: 'PO-1044', product: 'Mechanical Keyboard', sku: 'MK-2024-017',
    qty: 75, supplier: 'Global Parts Inc.',
    predictedStockout: '22 Jun 2025', recommendedQty: 100, estimatedCost: '$4,200.00',
  },
];

interface POHistory {
  id: string;
  product: string;
  supplier: string;
  qty: number;
  total: string;
  status: string;
  created: string;
  approvedBy: string;
}

const poHistory: POHistory[] = [
  { id: 'PO-1043', product: 'USB-C Hub', supplier: 'Warehouse Direct', qty: 100, total: '$1,800.00', status: 'Approved', created: '01 Jun 2025', approvedBy: 'John Doe' },
  { id: 'PO-1045', product: 'Monitor Stand', supplier: 'Local Distributors', qty: 50, total: '$950.00', status: 'Approved', created: '30 May 2025', approvedBy: 'John Doe' },
  { id: 'PO-1046', product: 'Webcam HD', supplier: 'TechSupply Co.', qty: 150, total: '$2,800.00', status: 'Sent', created: '28 May 2025', approvedBy: '\u2014' },
];

const historyColumns: Column<POHistory>[] = [
  { key: 'po', label: 'PO #', width: '100px', render: (r) => <span className="text-mono text-ink-muted">{r.id}</span> },
  { key: 'product', label: 'Product', render: (r) => <span className="truncate block">{r.product}</span> },
  { key: 'supplier', label: 'Supplier', width: '150px', render: (r) => <span className="truncate block text-ink-muted">{r.supplier}</span> },
  { key: 'qty', label: 'Qty', align: 'right', width: '60px', render: (r) => <span className="tabular-nums">{r.qty}</span> },
  { key: 'total', label: 'Total', align: 'right', width: '100px', render: (r) => <span className="tabular-nums">{r.total}</span> },
  { key: 'status', label: 'Status', width: '120px', render: (r) => <Badge>{r.status}</Badge> },
  { key: 'created', label: 'Created', width: '110px', render: (r) => <span className="text-caption text-ink-muted tabular-nums">{r.created}</span> },
  { key: 'approvedBy', label: 'Approved By', width: '120px', render: (r) => <span className="text-caption text-ink-muted">{r.approvedBy}</span> },
];

function POApprovalCard({ po }: { po: PendingPO }) {
  return (
    <div className="bg-canvas border-l-[3px] border-l-orange-600 rounded-lg shadow-elevated overflow-hidden">
      <div className="p-6 pb-4 border-b border-hairline">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-card-title text-ink">Purchase Order Draft</h3>
            <Badge variant="AI Generated" />
        </div>
        <p className="text-caption text-ink-muted">{po.id} — {po.product}</p>
      </div>

      <div className="p-6 space-y-3">
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
            <p className="text-body text-red-600 mt-0.5 tabular-nums">{po.predictedStockout}</p>
          </div>
          <div>
            <p className="text-caption text-ink-muted">Estimated cost</p>
            <p className="text-[16px] font-medium text-ink mt-0.5 tabular-nums">{po.estimatedCost}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 pt-2">
          <p className="text-caption text-ink-muted">Recommended qty:</p>
          <input
            type="number"
            defaultValue={po.recommendedQty}
            className="w-20 h-8 px-2 rounded-md border border-hairline bg-canvas text-body text-ink tabular-nums hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
            aria-label="Recommended quantity"
          />
        </div>

        <details className="group">
          <summary className="text-caption text-ink-muted cursor-pointer hover:text-ink transition-colors">
            Why did the AI flag this?
          </summary>
          <div className="mt-2 p-3 rounded-md bg-purple-50 border-l-2 border-purple-100">
            <p className="text-caption text-ink-muted italic leading-relaxed">
              {po.product} has a 30-day moving average of 185 units. Current stock of 28 units will last approximately 5 days based on current velocity. The AI recommends ordering {po.recommendedQty} units to maintain 30 days of buffer stock.
            </p>
          </div>
        </details>
      </div>

      <div className="flex items-center gap-3 p-6 pt-4 border-t border-hairline">
        <Button variant="primary" size="md" className="flex-1 bg-green-600 hover:bg-green-800">
          <Check className="w-4 h-4" /> Approve
        </Button>
        <Button variant="utility" size="md"><Pencil className="w-4 h-4" /> Edit Qty</Button>
        <Button variant="ghost" size="md" className="text-red-600 hover:bg-red-50"><X className="w-4 h-4" /> Reject</Button>
      </div>
    </div>
  );
}

export default function PurchasingPage() {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-page-heading text-ink">Purchase Orders</h1>
          <p className="text-body text-ink-muted mt-1">Keep the shelves stocked — approve, edit, and track supplier orders</p>
        </div>
        <Button variant="primary" size="md"><Plus className="w-4 h-4" /> New Order</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Pending Approval" subtitle={`${pendingPOs.length} orders awaiting review`}>
          {pendingPOs.length === 0 ? (
            <EmptyState
              icon={ShoppingCart}
              heading="All caught up on approvals"
              body="The AI's watching your stock levels — new purchase orders will appear here when something needs restocking."
            />
          ) : (
            <div className="space-y-3">
              {pendingPOs.map((po) => (
                <div key={po.id} className="flex items-start gap-3 p-3 rounded-md border border-hairline hover:bg-canvas-soft transition-colors cursor-pointer">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-body font-medium text-ink truncate">{po.product}</span>
                      <Badge variant="AI Generated" />
                    </div>
                    <p className="text-caption text-ink-muted mt-0.5 tabular-nums">{po.qty} units — {po.supplier}</p>
                  </div>
                  <span className="text-mono text-ink-muted shrink-0">{po.id}</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {pendingPOs[0] && <POApprovalCard po={pendingPOs[0]} />}
      </div>

      <Card title="PO History">
        <DataTable
          columns={historyColumns}
          data={poHistory}
          keyExtractor={(r) => r.id}
          caption="Purchase order history"
        />
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-hairline">
          <span className="text-caption text-ink-muted tabular-nums">Showing 1–3 of 3 results</span>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" disabled>Previous</Button>
            <Button variant="secondary" size="sm" disabled>Next</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
