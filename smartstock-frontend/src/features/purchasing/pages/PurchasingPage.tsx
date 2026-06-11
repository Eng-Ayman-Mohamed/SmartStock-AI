import { ShoppingCart, Plus } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import EmptyState from '../../../shared/components/EmptyState';
import DataTable from '../../../shared/components/DataTable';
import type { Column } from '../../../shared/components/DataTable';
import POApprovalCard from '../components/POApprovalCard';
import { usePendingPOs } from '../hooks/usePurchasing';
import type { PendingPO } from '../types';

const mockPendingPOs: PendingPO[] = [
  {
    id: 'PO-1042', product: 'Wireless Mouse', sku: 'WM-2024-001',
    supplier: 'TechSupply Co.',
    predicted_stockout: '15 Jun 2025', recommended_qty: 250,
    unit_cost: 21.25, estimated_total_cost: '$5,312.50',
    agent_reasoning: 'Wireless Mouse has a 30-day moving average of 185 units. Current stock of 28 units will last approximately 5 days based on current velocity. The AI recommends ordering 250 units to maintain 30 days of buffer stock.',
  },
  {
    id: 'PO-1044', product: 'Mechanical Keyboard', sku: 'MK-2024-017',
    supplier: 'Global Parts Inc.',
    predicted_stockout: '22 Jun 2025', recommended_qty: 100,
    unit_cost: 42.00, estimated_total_cost: '$4,200.00',
    agent_reasoning: null,
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

export default function PurchasingPage() {
  const { data: pendingPOsData, isLoading: isPendingLoading, isError } = usePendingPOs();
  const pendingPOs = isPendingLoading ? mockPendingPOs : (pendingPOsData ?? []);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-page-heading text-ink">Purchase Orders</h1>
          <p className="text-body text-ink-muted mt-1">Keep the shelves stocked — approve, edit, and track supplier orders</p>
        </div>
        <Button variant="primary" size="md"><Plus className="w-4 h-4" /> New Order</Button>
      </div>

      {isError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800">
          Failed to load pending purchase orders.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Pending Approval" subtitle={`${pendingPOs.length} orders awaiting review`}>
          {pendingPOs.length === 0 && !isError ? (
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
                    <p className="text-caption text-ink-muted mt-0.5 tabular-nums">{po.recommended_qty} units — {po.supplier}</p>
                  </div>
                  <span className="text-mono text-ink-muted shrink-0">{po.id}</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {pendingPOs[0] && <POApprovalCard key={pendingPOs[0].id} po={pendingPOs[0]} readOnly={isPendingLoading} />}
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
