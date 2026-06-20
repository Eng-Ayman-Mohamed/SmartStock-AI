import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Package,
  PackagePlus,
  PencilLine,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../../../lib/axios";
import { useDebounce } from "../../../shared/hooks/useDebounce";
import { usePagination } from "../../../shared/hooks/usePagination";
import { useAuthStore } from "../../../store/authStore";
import Card from "../../../shared/components/Card";
import Button from "../../../shared/components/Button";
import EmptyState from "../../../shared/components/EmptyState";
import Badge from "../../../shared/components/Badge";
import Skeleton from "../../../shared/components/Skeleton";
import Modal from "../../../shared/components/Modal";
import DataTable from "../../../shared/components/DataTable";
import type { Column } from "../../../shared/components/DataTable";
import { useToastStore } from "../../../store/toastStore";
import { useInventory } from "../hooks/useInventory";
import type { Product } from "../hooks/useInventory";
import AddEditProductModal from "../components/AddEditProductModal";
import AdjustStockModal from "../components/AdjustStockModal";

type Status = "In Stock" | "Low Stock" | "Out of Stock";

function statusFor(quantity: number, reorderPoint: number): Status {
  if (quantity <= 0) return "Out of Stock";
  if (quantity < reorderPoint) return "Low Stock";
  return "In Stock";
}

export default function InventoryPage() {
  const [searchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [statusFilter, setStatusFilter] = useState(
    searchParams.get("status") ?? "",
  );
  const [categoryFilter, setCategoryFilter] = useState(
    searchParams.get("category") ?? "",
  );
  const supplierId = searchParams.get("supplierId") ?? "";
  const [page, setPage] = useState(Number(searchParams.get("page") ?? 1));
  const [sortField, setSortField] = useState(searchParams.get("sort") ?? "");
  const [sortOrder, setSortOrder] = useState(searchParams.get("order") ?? "");
  const debouncedSearch = useDebounce(search, 300);
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const canManage = user?.role === "manager" || user?.role === "admin";
  const canDelete = user?.role === "admin";

  const [editingProduct, setEditingProduct] = useState<Product | "new" | null>(
    null,
  );
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [adjustingStock, setAdjustingStock] = useState<{
    stockId: number;
    skuCode: string;
  } | null>(null);

  const addToast = useToastStore((s) => s.addToast);

  function handleSort(key: string) {
    if (sortField === key && sortOrder === "asc") {
      setSortOrder("desc");
    } else if (sortField === key && sortOrder === "desc") {
      setSortField("");
      setSortOrder("");
    } else {
      setSortField(key);
      setSortOrder("asc");
    }
    setPage(1);
  }

  const inventoryQuery = useInventory({
    search: debouncedSearch,
    statusFilter,
    supplierId,
    sortField,
    sortOrder,
    page,
    categoryFilter,
  });

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const res = await api.get("/inventory/categories/", {
        params: { page_size: 100 },
      });
      const data = res.data;
      if (data && typeof data === "object" && "results" in data) {
        return data.results as Array<{ id: number; name: string }>;
      }
      return Array.isArray(data) ? data : [];
    },
    staleTime: 5 * 60 * 1000,
  });

  const saveProduct = useMutation({
    mutationFn: async ({
      product,
      data,
    }: {
      product?: Product;
      data: { name: string; description: string; reorder_point: number; safety_stock: number };
    }) => {
      if (product) {
        await api.patch(`/inventory/products/${product.id}/`, data);
      } else {
        await api.post("/inventory/products/", data);
      }
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      setEditingProduct(null);
      addToast(
        variables.product ? `Updated ${variables.product.name}` : "Product created",
        "success",
      );
    },
    onError: () => {
      addToast("Failed to save product", "error");
    },
  });

  const adjustStock = useMutation({
    mutationFn: async ({
      stockId,
      delta,
      reason,
    }: {
      stockId: number;
      delta: number;
      reason: string;
    }) => {
      await api.patch(`/inventory/stock-levels/${stockId}/adjust-stock/`, {
        quantity_delta: delta,
        reason,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      setAdjustingStock(null);
      addToast("Stock adjusted", "success");
    },
    onError: () => {
      addToast("Failed to adjust stock", "error");
    },
  });

  const deleteProduct = useMutation({
    mutationFn: async (product: Product) => {
      await api.delete(`/inventory/products/${product.id}/`);
    },
    onSuccess: (_, product) => {
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      setDeletingProduct(null);
      addToast(`Deleted ${product.name}`, "success");
    },
    onError: () => {
      addToast("Failed to delete product", "error");
    },
  });


  const rows = useMemo(() => {
    return inventoryQuery.products.flatMap((product) => {
      const skus = product.skus.length
        ? product.skus
        : [{ id: 0, code: "No SKU", stock_level_id: null }];
      return skus.map((sku) => {
        const quantity = sku.quantity_on_hand ?? 0;
        const reorderPoint = sku.stock_reorder_point ?? product.reorder_point;
        const status = statusFor(quantity, reorderPoint);
        return {
          product,
          sku,
          quantity,
          quantity_reserved: sku.quantity_reserved ?? 0,
          reorderPoint,
          status,
          stockId: sku.stock_level_id ?? 0,
        };
      });
    });
  }, [inventoryQuery.products]);

  const totalProducts = inventoryQuery.pagination.total;
  const currentPageSize = inventoryQuery.pagination.perPage;
  const pagination = usePagination({
    total: totalProducts,
    pageSize: currentPageSize,
    currentPage: page,
  });

  type Row = (typeof rows)[number];

  const columns = useMemo<Column<Row>[]>(() => [
    {
      key: "sku",
      label: "SKU",
      width: "130px",
      sortable: true,
      sortOrder: sortField === "sku" ? (sortOrder as "asc" | "desc") : undefined,
      render: (r) => (
        <span className="text-mono text-ink-secondary">{r.sku.code}</span>
      ),
    },
    {
      key: "product",
      label: "Product",
      sortable: true,
      sortOrder: sortField === "product" ? (sortOrder as "asc" | "desc") : undefined,
      render: (r) => <span className="truncate block">{r.product.name}</span>,
    },
    {
      key: "category",
      label: "Category",
      width: "130px",
      sortable: true,
      sortOrder: sortField === "category" ? (sortOrder as "asc" | "desc") : undefined,
      render: (r) => (
        <span className="truncate block text-ink-muted">
          {r.product.category_name ?? "Unassigned"}
        </span>
      ),
    },
    {
      key: "qty",
      label: "On Hand",
      align: "right",
      width: "160px",
      sortable: true,
      sortOrder: sortField === "qty" ? (sortOrder as "asc" | "desc") : undefined,
      render: (r) => (
        <div className="flex items-center gap-2 justify-end">
          <span className="tabular-nums">{r.quantity}</span>
          <div className="w-16 h-2 rounded-full bg-hairline overflow-hidden shrink-0">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                r.quantity <= 0
                  ? "bg-red-500 animate-pulse"
                  : r.quantity < r.reorderPoint
                    ? "bg-amber-500"
                    : "bg-green-500"
              }`}
              style={{
                width: `${Math.min(100, (r.quantity / Math.max(r.reorderPoint, 1)) * 100)}%`,
              }}
            />
          </div>
        </div>
      ),
    },
    {
      key: "reserved",
      label: "Reserved",
      align: "right",
      width: "80px",
      sortable: true,
      sortOrder: sortField === "reserved" ? (sortOrder as "asc" | "desc") : undefined,
      render: (r) => (
        <span className="tabular-nums">{r.quantity_reserved ?? 0}</span>
      ),
    },
    {
      key: "reorder",
      label: "Reorder",
      align: "right",
      width: "80px",
      sortable: true,
      sortOrder: sortField === "reorder" ? (sortOrder as "asc" | "desc") : undefined,
      render: (r) => <span className="tabular-nums">{r.reorderPoint}</span>,
    },
    {
      key: "supplier",
      label: "Supplier",
      sortable: true,
      sortOrder: sortField === "supplier" ? (sortOrder as "asc" | "desc") : undefined,
      render: (r) => (
        <span className="truncate block text-ink-muted">
          {r.product.supplier_name ?? "Unassigned"}
        </span>
      ),
    },
    {
      key: "status",
      label: "Status",
      width: "120px",
      sortable: true,
      sortOrder: sortField === "status" ? (sortOrder as "asc" | "desc") : undefined,
      render: (r) => <Badge variant={r.status}>{r.status}</Badge>,
    },
    {
      key: "actions",
      label: "Actions",
      align: "right",
      width: "160px",
      render: (r) => (
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-11 w-11 px-0 border border-hairline text-ink-muted hover:text-brand-700 hover:border-brand-200 dark:hover:text-brand-300 dark:hover:border-brand-600"
            onClick={() => setEditingProduct(r.product)}
            disabled={!canManage}
            aria-label={`Edit ${r.product.name}`}
            title={canManage ? "Edit product" : "Manager role required"}
          >
            <PencilLine className="w-5 h-5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-11 w-11 px-0 border border-hairline text-ink-muted hover:text-green-700 hover:border-green-200 dark:hover:text-green-300 dark:hover:border-green-600"
            onClick={() =>
              setAdjustingStock({ stockId: r.stockId, skuCode: r.sku.code })
            }
            disabled={!canManage || !r.stockId}
            aria-label={`Adjust stock for ${r.sku.code}`}
            title={
              !canManage
                ? "Manager role required"
                : r.stockId
                  ? "Adjust stock"
                  : "No stock record"
            }
          >
            <PackagePlus className="w-5 h-5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-11 w-11 px-0 border border-hairline text-ink-muted hover:text-red-700 hover:border-red-200 dark:hover:text-red-300 dark:hover:border-red-600"
            onClick={() => setDeletingProduct(r.product)}
            disabled={!canDelete}
            aria-label={`Delete ${r.product.name}`}
            title={canDelete ? "Delete product" : "Admin role required"}
          >
            <Trash2 className="w-5 h-5" />
          </Button>
        </div>
      ),
    },
  ], [sortField, sortOrder, canDelete, canManage]);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-page-heading text-ink">Inventory</h1>
          <p className="text-body text-ink-muted mt-1">
            Stock's lookin' thin in places —{" "}
            {inventoryQuery.lowStock.length || "some"} SKUs could use a
            top-up.
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          onClick={() => setEditingProduct("new")}
          disabled={!canManage}
        >
          <Plus className="w-4 h-4" /> Add Product
        </Button>
      </div>

      {inventoryQuery.lowStock.length ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {inventoryQuery.lowStock.slice(0, 6).map((item) => (
            <Card key={item.id}>
              <p className="text-body font-medium text-ink truncate">
                {item.product_name}
              </p>
              <p className="text-caption text-ink-muted mt-1">
                <span className="font-mono">{item.sku_code}</span>
                <span className="tabular-nums">
                  {" "}
                  &middot; {item.quantity}/{item.reorder_point}
                </span>
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-faint"
            aria-hidden="true"
          />
          <input
            type="text"
            placeholder="Search by product name or SKU..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full h-9 pl-10 pr-4 rounded-full border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors duration-150"
            aria-label="Search products"
          />
        </div>
        <select
          className="h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink-secondary hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors duration-150"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          aria-label="Status filter"
        >
          <option value="">All statuses</option>
          <option>In Stock</option>
          <option>Low Stock</option>
          <option>Out of Stock</option>
        </select>
        <select
          className="h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink-secondary hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors duration-150"
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(e.target.value);
            setPage(1);
          }}
          aria-label="Category filter"
        >
          <option value="">All categories</option>
          {categoriesQuery.data?.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>
      </div>

      {inventoryQuery.isError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800 dark:border-red-800 dark:bg-red-900/30 dark:text-red-200 flex items-center justify-between">
          <span>Failed to load inventory data.</span>
          <button onClick={() => inventoryQuery.refetch()} className="underline text-sm font-medium">Retry</button>
        </div>
      )}

      <Card noPadding>
        {inventoryQuery.isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3, 4, 5].map((item) => (
              <Skeleton key={item} className="h-10" />
            ))}
          </div>
        ) : rows.length === 0 && !inventoryQuery.isError ? (
          <EmptyState
            icon={Package}
            heading="No products yet"
            body="Add your first product to start tracking inventory."
            actionLabel={canManage ? "Add Product" : undefined}
            onAction={canManage ? () => setEditingProduct("new") : undefined}
          />
        ) : (
          <div
            className={
              inventoryQuery.isFetching
                ? "opacity-70 transition-opacity"
                : "transition-opacity"
            }
          >
            <DataTable
              columns={columns}
              data={rows}
              keyExtractor={(r) => `${r.product.id}-${r.sku.code}`}
              caption="Inventory products and stock levels"
              onSort={handleSort}
              pagination={{
                ...pagination,
                currentPage: page,
                total: totalProducts,
                onPageChange: (p) => setPage(p),
              }}
            />
          </div>
        )} 
      </Card>

      <AddEditProductModal
        key={editingProduct === "new" ? "new" : editingProduct?.id ?? "none"}
        open={editingProduct !== null}
        product={editingProduct}
        onClose={() => setEditingProduct(null)}
        onSave={(data) =>
          saveProduct.mutate({
            product: editingProduct && editingProduct !== "new" ? editingProduct : undefined,
            data,
          })
        }
        isPending={saveProduct.isPending}
      />

      <Modal
        open={deletingProduct !== null}
        onClose={() => setDeletingProduct(null)}
        title="Delete Product"
        footer={
          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              size="md"
              onClick={() => setDeletingProduct(null)}
            >
              <X className="w-4 h-4" /> Cancel
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={() => {
                if (deletingProduct) deleteProduct.mutate(deletingProduct);
              }}
              disabled={deleteProduct.isPending}
            >
              <Trash2 className="w-4 h-4" /> Delete
            </Button>
          </div>
        }
      >
        <p className="text-body text-ink-secondary">
          Are you sure you want to delete{" "}
          <strong>{deletingProduct?.name}</strong>? This action cannot be
          undone.
        </p>
      </Modal>

      <AdjustStockModal
        open={adjustingStock !== null}
        stockInfo={adjustingStock}
        onClose={() => setAdjustingStock(null)}
        onAdjust={({ delta, reason }) =>
          adjustStock.mutate({
            stockId: adjustingStock!.stockId,
            delta,
            reason,
          })
        }
        isPending={adjustStock.isPending}
      />
    </div>
  );
}
