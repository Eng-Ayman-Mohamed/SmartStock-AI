import { useMemo, useState } from "react";
import { ShoppingCart, Plus } from "lucide-react";
import Card from "../../../shared/components/Card";
import Button from "../../../shared/components/Button";
import Badge from "../../../shared/components/Badge";
import EmptyState from "../../../shared/components/EmptyState";
import Skeleton from "../../../shared/components/Skeleton";
import DataTable from "../../../shared/components/DataTable";
import type {
  Column,
  PaginationConfig,
} from "../../../shared/components/DataTable";
import POApprovalCard from "../components/POApprovalCard";
import { usePendingPOs, usePOHistory } from "../hooks/usePurchasing";
import type { POHistoryItem } from "../api";
import { usePagination } from "../../../shared/hooks/usePagination";

const PAGE_SIZE = 20;
const EMPTY_ARRAY: [] = [];

const historyColumns: Column<POHistoryItem>[] = [
  {
    key: "id",
    label: "PO #",
    width: "100px",
    render: (r) => <span className="text-mono text-ink-muted">{r.id}</span>,
  },
  {
    key: "product_name",
    label: "Product",
    render: (r) => <span className="truncate block">{r.product_name}</span>,
  },
  {
    key: "supplier",
    label: "Supplier",
    width: "150px",
    render: (r) => (
      <span className="truncate block text-ink-muted">{r.supplier}</span>
    ),
  },
  {
    key: "quantity",
    label: "Qty",
    align: "right",
    width: "60px",
    render: (r) => <span className="tabular-nums">{r.quantity}</span>,
  },
  {
    key: "total",
    label: "Total",
    align: "right",
    width: "100px",
    render: (r) => <span className="tabular-nums">{r.total}</span>,
  },
  {
    key: "status",
    label: "Status",
    width: "120px",
    render: (r) => <Badge>{r.status}</Badge>,
  },
  {
    key: "created_at",
    label: "Created",
    width: "110px",
    render: (r) => (
      <span className="text-caption text-ink-muted tabular-nums">
        {r.created_at}
      </span>
    ),
  },
  {
    key: "approved_by",
    label: "Approved By",
    width: "120px",
    render: (r) => (
      <span className="text-caption text-ink-muted">{r.approved_by}</span>
    ),
  },
];

export default function PurchasingPage() {
  const [selectedPoId, setSelectedPoId] = useState<string | null>(null);
  const [poPage, setPoPage] = useState(1);

  const {
    data: pendingPOsData,
    isLoading: isPendingLoading,
    isError,
  } = usePendingPOs();
  const {
    data: poHistoryData,
    isLoading: isHistoryLoading,
    isError: isHistoryError,
  } = usePOHistory(poPage, PAGE_SIZE);
  const pendingPOs = pendingPOsData?.results ?? EMPTY_ARRAY;
  const poHistory = poHistoryData?.results ?? EMPTY_ARRAY;

  // Derive selected PO: user's pick if it still exists in the list, otherwise the first PO
  const selectedPO = useMemo(() => {
    if (selectedPoId) {
      const found = pendingPOs.find((po) => po.id === selectedPoId);
      if (found) return found;
    }
    return pendingPOs[0] ?? null;
  }, [pendingPOs, selectedPoId]);

  const poTotalCount = poHistoryData?.count ?? 0;
  const poPagination = usePagination({
    total: poTotalCount,
    pageSize: PAGE_SIZE,
    currentPage: Math.min(poPage, Math.max(1, Math.ceil(poTotalCount / PAGE_SIZE))),
  });

  const poPaginationConfig: PaginationConfig = {
    currentPage: poPage,
    totalPages: poPagination.totalPages,
    total: poTotalCount,
    startItem: poPagination.startItem,
    endItem: poPagination.endItem,
    hasPrev: poPagination.hasPrev,
    hasNext: poPagination.hasNext,
    pages: poPagination.pages,
    onPageChange: (p) => setPoPage(p),
    itemLabel: "results",
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-page-heading text-ink">Purchase Orders</h1>
          <p className="text-body text-ink-muted mt-1">
            Keep the shelves stocked — approve, edit, and track supplier orders
          </p>
        </div>
        <Button variant="primary" size="md">
          <Plus className="w-4 h-4" /> New Order
        </Button>
      </div>

      {isError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800 dark:border-red-800 dark:bg-red-900/30 dark:text-red-200">
          Failed to load pending purchase orders.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <Card
          title="Pending Approval"
          subtitle={
            isPendingLoading
              ? undefined
              : `${pendingPOs.length} orders awaiting review`
          }
        >
          {isPendingLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : pendingPOs.length === 0 && !isError ? (
            <EmptyState
              icon={ShoppingCart}
              heading="All caught up on approvals"
              body="The AI's watching your stock levels — new purchase orders will appear here when something needs restocking."
            />
          ) : (
            <div className="max-h-[360px] overflow-y-auto overscroll-contain space-y-3">
              {pendingPOs.map((po) => {
                const isSelected = po.id === selectedPoId;
                return (
                  <div
                    key={po.id}
                    onClick={() => setSelectedPoId(po.id)}
                    className={`flex items-start gap-3 p-3 rounded-md border transition-colors cursor-pointer ${
                      isSelected
                        ? "border-brand-600 bg-brand-50 dark:border-brand-400 dark:bg-brand-900/30"
                        : "border-hairline hover:bg-canvas-soft"
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-body font-medium text-ink truncate">
                          {po.product}
                        </span>
                        <Badge variant="AI Generated" />
                      </div>
                      <p className="text-caption text-ink-muted mt-0.5 tabular-nums">
                        {po.recommended_qty} units — {po.supplier}
                      </p>
                    </div>
                    <span className="text-mono text-ink-muted shrink-0">
                      {po.id}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        {selectedPO && (
          <POApprovalCard
            key={selectedPO.id}
            po={selectedPO}
            readOnly={isPendingLoading}
          />
        )}
      </div>

      {isHistoryError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800 dark:border-red-800 dark:bg-red-900/30 dark:text-red-200">
          Failed to load purchase order history.
        </div>
      )}

      <Card title="PO History">
        {isHistoryLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        ) : (
          <DataTable
            columns={historyColumns}
            data={poHistory}
            keyExtractor={(r) => r.id}
            caption="Purchase order history"
            pagination={poPaginationConfig}
          />
        )}
      </Card>
    </div>
  );
}
