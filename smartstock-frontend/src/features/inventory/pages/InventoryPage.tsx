import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Package,
  PackagePlus,
  PencilLine,
  Plus,
  Search,
  Trash2,
  X,
} from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../../lib/axios';
import { useDebounce } from '../../../shared/hooks/useDebounce';
import { usePagination } from '../../../shared/hooks/usePagination';
import { useAuthStore } from '../../../store/authStore';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import EmptyState from '../../../shared/components/EmptyState';
import Badge from '../../../shared/components/Badge';
import Skeleton from '../../../shared/components/Skeleton';
import Modal from '../../../shared/components/Modal';
import DataTable from '../../../shared/components/DataTable';
import type { Column } from '../../../shared/components/DataTable';
import { useToastStore } from '../../../store/toastStore';

type Product = {
  id: number;
  name: string;
  description: string;
  category_name?: string | null;
  supplier_name?: string | null;
  reorder_point: number;
  safety_stock: number;
  skus: ProductSku[];
};

type ProductSku = {
  id: number;
  code: string;
  stock_level_id?: number | null;
  quantity_on_hand?: number;
  quantity_reserved?: number;
  stock_reorder_point?: number | null;
};

type LowStockItem = {
  id: number;
  product_name: string;
  sku_code: string;
  quantity: number;
  reorder_point: number;
};

type Status = 'In Stock' | 'Low Stock' | 'Out of Stock';

function unwrap<T>(payload: T | { data: T }): T {
  return payload && typeof payload === 'object' && 'data' in payload ? payload.data : payload;
}

type PaginationMeta = {
  page: number;
  total: number;
  perPage: number;
  next: string | null;
  previous: string | null;
};

const PAGE_SIZE = 20;

const statusParamByLabel: Record<Status, string> = {
  'In Stock': 'in_stock',
  'Low Stock': 'low_stock',
  'Out of Stock': 'out_of_stock',
};

function numberFromMeta(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function statusFor(quantity: number, reorderPoint: number): Status {
  if (quantity <= 0) return 'Out of Stock';
  if (quantity < reorderPoint) return 'Low Stock';
  return 'In Stock';
}

export default function InventoryPage() {
  const [searchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('search') ?? '');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') ?? '');
  const [page, setPage] = useState(Number(searchParams.get('page') ?? 1));
  const [sortField] = useState(searchParams.get('sort') ?? '');
  const [sortOrder] = useState(searchParams.get('order') ?? '');
  const debouncedSearch = useDebounce(search, 300);
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const canManage = user?.role === 'manager' || user?.role === 'admin';
  const canDelete = user?.role === 'admin';

  const [editingProduct, setEditingProduct] = useState<Product | 'new' | null>(null);
  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [adjustingStock, setAdjustingStock] = useState<{ stockId: number; skuCode: string } | null>(null);
  const [stockDelta, setStockDelta] = useState('');
  const [stockReason, setStockReason] = useState('');
  const [formName, setFormName] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formReorder, setFormReorder] = useState(10);
  const [formSafety, setFormSafety] = useState(10);

  const addToast = useToastStore((s) => s.addToast);

  const ordering = sortField ? (sortOrder === 'desc' ? `-${sortField}` : sortField) : '';
  const orderingParam = ordering ? { ordering } : {};

  const inventoryQuery = useQuery({
    queryKey: ['inventory', debouncedSearch, statusFilter, sortField, sortOrder, page],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: PAGE_SIZE, ...orderingParam };
      if (debouncedSearch) params.search = debouncedSearch;
      if (statusFilter) params.stock_status = statusParamByLabel[statusFilter as Status];
      const [productsRes, lowStockRes] = await Promise.all([
        api.get('/inventory/products/', { params }),
        api.get('/inventory/stock-levels/low_stock/'),
      ]);
      const products = unwrap<Product[]>(productsRes.data);
      const meta = productsRes._meta ?? {};

      return {
        products,
        pagination: {
          page: numberFromMeta(meta.page, page),
          total: numberFromMeta(meta.total, products.length),
          perPage: numberFromMeta(meta.per_page, PAGE_SIZE),
          next: typeof meta.next === 'string' ? meta.next : null,
          previous: typeof meta.previous === 'string' ? meta.previous : null,
        } satisfies PaginationMeta,
        lowStock: unwrap<LowStockItem[]>(lowStockRes.data),
      };
    },
    placeholderData: (previousData) => previousData,
  });

  const saveProduct = useMutation({
    mutationFn: async (product?: Product) => {
      const payload = {
        name: formName,
        description: formDescription,
        reorder_point: formReorder,
        safety_stock: formSafety,
      };
      if (product) {
        await api.patch(`/inventory/products/${product.id}/`, payload);
      } else {
        await api.post('/inventory/products/', payload);
      }
    },
    onSuccess: (_data, product) => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      setEditingProduct(null);
      addToast(product ? `Updated ${product.name}` : 'Product created', 'success');
    },
    onError: () => {
      addToast('Failed to save product', 'error');
    },
  });

  const adjustStock = useMutation({
    mutationFn: async ({ stockId, delta, reason }: { stockId: number; delta: number; reason: string }) => {
      await api.patch(`/inventory/stock-levels/${stockId}/adjust-stock/`, { quantity_delta: delta, reason });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      setAdjustingStock(null);
      setStockDelta('');
      setStockReason('');
      addToast('Stock adjusted', 'success');
    },
    onError: () => {
      addToast('Failed to adjust stock', 'error');
    },
  });

  const deleteProduct = useMutation({
    mutationFn: async (product: Product) => {
      await api.delete(`/inventory/products/${product.id}/`);
    },
    onSuccess: (_, product) => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      setDeletingProduct(null);
      addToast(`Deleted ${product.name}`, 'success');
    },
    onError: () => {
      addToast('Failed to delete product', 'error');
    },
  });

  function openNewProductForm() {
    setFormName('');
    setFormDescription('');
    setFormReorder(10);
    setFormSafety(10);
    setEditingProduct('new');
  }

  function openEditForm(product: Product) {
    setFormName(product.name);
    setFormDescription(product.description);
    setFormReorder(product.reorder_point);
    setFormSafety(product.safety_stock);
    setEditingProduct(product);
  }

  const rows = useMemo(() => {
    const data = inventoryQuery.data;
    if (!data) return [];

    return data.products
      .flatMap((product) => {
        const skus = product.skus.length ? product.skus : [{ id: 0, code: 'No SKU', stock_level_id: null }];
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
      })
      .filter((row) => !statusFilter || row.status === statusFilter);
  }, [inventoryQuery.data, statusFilter]);

  const totalProducts = inventoryQuery.data?.pagination.total ?? 0;
  const currentPageSize = inventoryQuery.data?.pagination.perPage ?? PAGE_SIZE;
  const pagination = usePagination({ total: totalProducts, pageSize: currentPageSize, currentPage: page });
  const firstVisibleItem = totalProducts === 0 ? 0 : pagination.startItem;
  const lastVisibleItem = totalProducts === 0 ? 0 : pagination.endItem;

  type Row = (typeof rows)[number];

  const columns: Column<Row>[] = [
    {
      key: 'sku',
      label: 'SKU',
      width: '130px',
      render: (r) => <span className="text-mono text-ink-secondary">{r.sku.code}</span>,
    },
    {
      key: 'product',
      label: 'Product',
      render: (r) => <span className="truncate block">{r.product.name}</span>,
    },
    {
      key: 'category',
      label: 'Category',
      width: '130px',
      render: (r) => <span className="truncate block text-ink-muted">{r.product.category_name ?? 'Unassigned'}</span>,
    },
    {
      key: 'qty',
      label: 'On Hand',
      align: 'right',
      width: '160px',
      render: (r) => (
        <div className="flex items-center gap-2 justify-end">
          <span className="tabular-nums">{r.quantity}</span>
          <div className="w-16 h-2 rounded-full bg-gray-100 overflow-hidden shrink-0">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                r.quantity <= 0
                  ? 'bg-red-500 animate-pulse'
                  : r.quantity < r.reorderPoint
                  ? 'bg-amber-500'
                  : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(100, (r.quantity / Math.max(r.reorderPoint, 1)) * 100)}%` }}
            />
          </div>
        </div>
      ),
    },
    {
      key: 'reserved',
      label: 'Reserved',
      align: 'right',
      width: '80px',
      render: (r) => <span className="tabular-nums">{r.quantity_reserved ?? 0}</span>,
    },
    {
      key: 'reorder',
      label: 'Reorder',
      align: 'right',
      width: '80px',
      render: (r) => <span className="tabular-nums">{r.reorderPoint}</span>,
    },
    {
      key: 'supplier',
      label: 'Supplier',
      render: (r) => <span className="truncate block text-ink-muted">{r.product.supplier_name ?? 'Unassigned'}</span>,
    },
    {
      key: 'status',
      label: 'Status',
      width: '120px',
      render: (r) => <Badge variant={r.status}>{r.status}</Badge>,
    },
    {
      key: 'actions',
      label: 'Actions',
      align: 'right',
      width: '150px',
      render: (r) => (
        <div className="flex items-center justify-end gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 px-0 border border-hairline text-ink-muted hover:text-brand-700 hover:border-brand-200"
            onClick={() => openEditForm(r.product)}
            disabled={!canManage}
            aria-label={`Edit ${r.product.name}`}
            title={canManage ? 'Edit product' : 'Manager role required'}
          >
            <PencilLine className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 px-0 border border-hairline text-ink-muted hover:text-green-700 hover:border-green-200"
            onClick={() => setAdjustingStock({ stockId: r.stockId, skuCode: r.sku.code })}
            disabled={!canManage || !r.stockId}
            aria-label={`Adjust stock for ${r.sku.code}`}
            title={!canManage ? 'Manager role required' : r.stockId ? 'Adjust stock' : 'No stock record'}
          >
            <PackagePlus className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 px-0 border border-hairline text-ink-muted hover:text-red-700 hover:border-red-200"
            onClick={() => setDeletingProduct(r.product)}
            disabled={!canDelete}
            aria-label={`Delete ${r.product.name}`}
            title={canDelete ? 'Delete product' : 'Admin role required'}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-page-heading text-ink">Inventory</h1>
          <p className="text-body text-ink-muted mt-1">Stock's lookin' thin in places — {inventoryQuery.data?.lowStock.length ?? 'some'} SKUs could use a top-up.</p>
        </div>
        <Button variant="primary" size="md" onClick={openNewProductForm} disabled={!canManage}>
          <Plus className="w-4 h-4" /> Add Product
        </Button>
      </div>

      {inventoryQuery.data?.lowStock.length ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {inventoryQuery.data.lowStock.slice(0, 6).map((item) => (
            <Card key={item.id}>
              <p className="text-body font-medium text-ink truncate">{item.product_name}</p>
              <p className="text-caption text-ink-muted mt-1">
                <span className="font-mono">{item.sku_code}</span>
                <span className="tabular-nums"> &middot; {item.quantity}/{item.reorder_point}</span>
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-faint" aria-hidden="true" />
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
      </div>

      {inventoryQuery.isError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800">
          Failed to load inventory data.
        </div>
      )}

      <Card noPadding>
        {inventoryQuery.isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3, 4, 5].map((item) => <Skeleton key={item} className="h-10" />)}
          </div>
        ) : rows.length === 0 ? (
          <EmptyState
            icon={Package}
            heading="No products yet"
            body="Add your first product to start tracking inventory."
            actionLabel={canManage ? 'Add Product' : undefined}
            onAction={canManage ? openNewProductForm : undefined}
          />
        ) : (
          <>
            <div className={inventoryQuery.isFetching ? 'opacity-70 transition-opacity' : 'transition-opacity'}>
              <DataTable
                columns={columns}
                data={rows}
                keyExtractor={(r) => `${r.product.id}-${r.sku.code}`}
                caption="Inventory products and stock levels"
              />
            </div>
            <div className="flex flex-col gap-3 border-t border-hairline px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-caption text-ink-muted">
                Showing <span className="tabular-nums text-ink-secondary">{firstVisibleItem}</span>
                {' - '}
                <span className="tabular-nums text-ink-secondary">{lastVisibleItem}</span>
                {' of '}
                <span className="tabular-nums text-ink-secondary">{totalProducts}</span> products
              </p>
              <div className="flex items-center gap-1" aria-label="Inventory pagination">
                <Button
                  variant="utility"
                  size="sm"
                  className="h-8 w-8 px-0"
                  onClick={() => setPage(1)}
                  disabled={!pagination.hasPrev}
                  aria-label="First page"
                  title="First page"
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="utility"
                  size="sm"
                  className="h-8 w-8 px-0"
                  onClick={() => setPage((value) => Math.max(1, value - 1))}
                  disabled={!pagination.hasPrev}
                  aria-label="Previous page"
                  title="Previous page"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                {pagination.pages.map((pageNumber, index) =>
                  pageNumber === -1 ? (
                    <span key={`gap-${index}`} className="flex h-8 w-8 items-center justify-center text-caption text-ink-faint">
                      ...
                    </span>
                  ) : (
                    <Button
                      key={pageNumber}
                      variant={pageNumber === page ? 'primary' : 'utility'}
                      size="sm"
                      className="h-8 w-8 px-0 tabular-nums"
                      onClick={() => setPage(pageNumber)}
                      aria-label={`Page ${pageNumber}`}
                      title={`Page ${pageNumber}`}
                    >
                      {pageNumber}
                    </Button>
                  )
                )}
                <Button
                  variant="utility"
                  size="sm"
                  className="h-8 w-8 px-0"
                  onClick={() => setPage((value) => Math.min(pagination.totalPages, value + 1))}
                  disabled={!pagination.hasNext}
                  aria-label="Next page"
                  title="Next page"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="utility"
                  size="sm"
                  className="h-8 w-8 px-0"
                  onClick={() => setPage(pagination.totalPages)}
                  disabled={!pagination.hasNext}
                  aria-label="Last page"
                  title="Last page"
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>

      <Modal
        open={editingProduct !== null}
        onClose={() => setEditingProduct(null)}
        title={editingProduct && editingProduct !== 'new' ? 'Edit Product' : 'New Product'}
        footer={
          <div className="flex items-center gap-3">
            <Button variant="secondary" size="md" onClick={() => setEditingProduct(null)}>
              <X className="w-4 h-4" /> Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={() => saveProduct.mutate(editingProduct && editingProduct !== 'new' ? editingProduct : undefined)}
              disabled={!formName.trim() || saveProduct.isPending}
            >
              <Plus className="w-4 h-4" /> {editingProduct ? 'Save Changes' : 'Create Product'}
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-caption text-ink-muted mb-1">Product Name</label>
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
            <label className="block text-caption text-ink-muted mb-1">Description</label>
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
              <label className="block text-caption text-ink-muted mb-1">Reorder Point</label>
              <input
                type="number"
                value={formReorder}
                onChange={(e) => setFormReorder(Number(e.target.value))}
                className="w-full h-9 px-3 rounded-full border border-hairline bg-canvas text-body text-ink tabular-nums hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
                aria-label="Reorder point"
              />
            </div>
            <div>
              <label className="block text-caption text-ink-muted mb-1">Safety Stock</label>
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

      <Modal
        open={deletingProduct !== null}
        onClose={() => setDeletingProduct(null)}
        title="Delete Product"
        footer={
          <div className="flex items-center gap-3">
            <Button variant="secondary" size="md" onClick={() => setDeletingProduct(null)}>
              <X className="w-4 h-4" /> Cancel
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={() => { if (deletingProduct) deleteProduct.mutate(deletingProduct); }}
              disabled={deleteProduct.isPending}
            >
              <Trash2 className="w-4 h-4" /> Delete
            </Button>
          </div>
        }
      >
        <p className="text-body text-ink-secondary">
          Are you sure you want to delete <strong>{deletingProduct?.name}</strong>? This action cannot be undone.
        </p>
      </Modal>

      <Modal
        open={adjustingStock !== null}
        onClose={() => { setAdjustingStock(null); setStockDelta(''); setStockReason(''); }}
        title={`Adjust Stock — ${adjustingStock?.skuCode ?? ''}`}
        footer={
          <div className="flex items-center gap-3">
            <Button variant="secondary" size="md" onClick={() => { setAdjustingStock(null); setStockDelta(''); setStockReason(''); }}>
              <X className="w-4 h-4" /> Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={() => {
                if (adjustingStock && stockDelta) {
                  adjustStock.mutate({ stockId: adjustingStock.stockId, delta: Number(stockDelta), reason: stockReason });
                }
              }}
              disabled={adjustStock.isPending || !stockDelta}
            >
              <ArrowUpDown className="w-4 h-4" /> Adjust
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-caption font-medium text-ink-secondary mb-1">Quantity Delta</label>
            <input
              type="number"
              value={stockDelta}
              onChange={(e) => setStockDelta(e.target.value)}
              className="w-full h-9 px-3 rounded-md border border-gray-200 bg-white text-body text-gray-800 focus:border-brand-600 focus:outline-none"
              placeholder="e.g. 10 or -5"
            />
            <p className="text-caption text-ink-muted mt-1">Positive to add stock, negative to remove.</p>
          </div>
          <div>
            <label className="block text-caption font-medium text-ink-secondary mb-1">Reason (optional)</label>
            <input
              type="text"
              value={stockReason}
              onChange={(e) => setStockReason(e.target.value)}
              className="w-full h-9 px-3 rounded-md border border-gray-200 bg-white text-body text-gray-800 focus:border-brand-600 focus:outline-none"
              placeholder="e.g. Received shipment"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
