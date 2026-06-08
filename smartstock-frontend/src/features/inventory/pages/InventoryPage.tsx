import { useMemo, useState } from 'react';
import { Edit3, Package, Plus, Search, Trash2 } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../../../lib/axios';
import { useDebounce } from '../../../shared/hooks/useDebounce';
import { useAuthStore } from '../../../store/authStore';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import EmptyState from '../../../shared/components/EmptyState';
import Badge from '../../../shared/components/Badge';
import Skeleton from '../../../shared/components/Skeleton';

type Product = {
  id: number;
  name: string;
  description: string;
  category_name?: string | null;
  supplier_name?: string | null;
  reorder_point: number;
  safety_stock: number;
  skus: { id: number; code: string }[];
};

type StockLevel = {
  id: number;
  sku: number;
  sku_code: string;
  product_name: string;
  quantity?: number;
  quantity_on_hand?: number;
  reorder_point: number;
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

function statusFor(quantity: number, reorderPoint: number): Status {
  if (quantity <= 0) return 'Out of Stock';
  if (quantity < reorderPoint) return 'Low Stock';
  return 'In Stock';
}

export default function InventoryPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const canManage = user?.role === 'manager' || user?.role === 'admin';
  const canDelete = user?.role === 'admin';

  const inventoryQuery = useQuery({
    queryKey: ['inventory', debouncedSearch],
    queryFn: async () => {
      const params = debouncedSearch ? { search: debouncedSearch, page_size: 100 } : { page_size: 100 };
      const [productsRes, stockRes, lowStockRes] = await Promise.all([
        api.get('/inventory/products/', { params }),
        api.get('/inventory/stock-levels/', { params: { page_size: 100 } }),
        api.get('/inventory/stock-levels/low_stock/'),
      ]);

      return {
        products: unwrap<Product[]>(productsRes.data),
        stockLevels: unwrap<StockLevel[]>(stockRes.data),
        lowStock: unwrap<LowStockItem[]>(lowStockRes.data),
      };
    },
  });

  const saveProduct = useMutation({
    mutationFn: async (product?: Product) => {
      const name = window.prompt('Product name', product?.name ?? '');
      if (!name) return;
      const payload = {
        name,
        description: product?.description ?? '',
        reorder_point: product?.reorder_point ?? 10,
        safety_stock: product?.safety_stock ?? 0,
      };
      if (product) {
        await api.patch(`/inventory/products/${product.id}/`, payload);
      } else {
        await api.post('/inventory/products/', payload);
      }
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inventory'] }),
  });

  const deleteProduct = useMutation({
    mutationFn: async (product: Product) => {
      if (!window.confirm(`Delete ${product.name}?`)) return;
      await api.delete(`/inventory/products/${product.id}/`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inventory'] }),
  });

  const rows = useMemo(() => {
    const data = inventoryQuery.data;
    if (!data) return [];
    const stockBySkuId = new Map(data.stockLevels.map((stock) => [stock.sku, stock]));

    return data.products
      .flatMap((product) => {
        const skus = product.skus.length ? product.skus : [{ id: 0, code: 'No SKU' }];
        return skus.map((sku) => {
          const stock = stockBySkuId.get(sku.id);
          const quantity = stock?.quantity ?? stock?.quantity_on_hand ?? 0;
          const reorderPoint = stock?.reorder_point ?? product.reorder_point;
          const status = statusFor(quantity, reorderPoint);
          return { product, sku, quantity, reorderPoint, status };
        });
      })
      .filter((row) => !statusFilter || row.status === statusFilter);
  }, [inventoryQuery.data, statusFilter]);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-page-heading text-gray-900">Inventory</h1>
          <p className="text-body text-gray-600 mt-1">Manage products, stock levels, and low-stock alerts</p>
        </div>
        <Button variant="primary" size="md" onClick={() => saveProduct.mutate(undefined)} disabled={!canManage}>
          <Plus className="w-4 h-4" /> Add Product
        </Button>
      </div>

      {inventoryQuery.data?.lowStock.length ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {inventoryQuery.data.lowStock.slice(0, 6).map((item) => (
            <Card key={item.id}>
              <p className="text-body font-medium text-gray-900 truncate">{item.product_name}</p>
              <p className="text-caption text-gray-600 mt-1">
                <span className="font-mono">{item.sku_code}</span>
                <span className="tabular-nums"> · {item.quantity}/{item.reorder_point}</span>
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
          <input
            type="text"
            placeholder="Search by product name or SKU..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-9 pl-10 pr-4 rounded-md border-[0.5px] border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 hover:border-gray-400 focus:border-brand-600 focus:outline-none transition-colors duration-150"
            aria-label="Search products"
          />
        </div>
        <select
          className="h-9 px-3 rounded-md border-[0.5px] border-gray-100 bg-white text-body text-gray-600 hover:border-gray-400 focus:border-brand-600 focus:outline-none transition-colors duration-150"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Status filter"
        >
          <option value="">All statuses</option>
          <option>In Stock</option>
          <option>Low Stock</option>
          <option>Out of Stock</option>
        </select>
      </div>

      {inventoryQuery.isError && (
        <div className="rounded-md border-[0.5px] border-red-200 bg-red-50 px-4 py-3 text-body text-red-800">
          Failed to load inventory data.
        </div>
      )}

      <Card noPadding>
        {inventoryQuery.isLoading ? (
          <div className="p-5 space-y-3">
            {[1, 2, 3, 4, 5].map((item) => <Skeleton key={item} className="h-10" />)}
          </div>
        ) : rows.length === 0 ? (
          <EmptyState
            icon={Package}
            heading="No products yet"
            body="Add your first product to start tracking inventory."
            actionLabel={canManage ? 'Add Product' : undefined}
            onAction={canManage ? () => saveProduct.mutate(undefined) : undefined}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] table-fixed border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b-[1px] border-gray-100">
                  {['SKU', 'Product', 'Category', 'On Hand', 'Reorder', 'Supplier', 'Status', 'Actions'].map((heading) => (
                    <th key={heading} className="h-9 px-3 text-caption font-medium text-gray-600 uppercase tracking-[0.05em] text-left">
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={`${row.product.id}-${row.sku.code}`} className="bg-white border-b-[0.5px] border-gray-100 hover:bg-gray-50">
                    <td className="h-11 px-3 text-body text-gray-800 truncate font-mono">{row.sku.code}</td>
                    <td className="h-11 px-3 text-body text-gray-900 truncate">{row.product.name}</td>
                    <td className="h-11 px-3 text-body text-gray-600 truncate">{row.product.category_name ?? 'Unassigned'}</td>
                    <td className="h-11 px-3 text-body text-gray-800 tabular-nums">{row.quantity}</td>
                    <td className="h-11 px-3 text-body text-gray-800 tabular-nums">{row.reorderPoint}</td>
                    <td className="h-11 px-3 text-body text-gray-600 truncate">{row.product.supplier_name ?? 'Unassigned'}</td>
                    <td className="h-11 px-3"><Badge variant={row.status}>{row.status}</Badge></td>
                    <td className="h-11 px-3">
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" className="w-7 px-0" onClick={() => saveProduct.mutate(row.product)} disabled={!canManage} aria-label="Edit product">
                          <Edit3 className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="w-7 px-0" onClick={() => deleteProduct.mutate(row.product)} disabled={!canDelete} aria-label="Delete product">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
