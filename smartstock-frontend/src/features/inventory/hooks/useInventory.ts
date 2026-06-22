import { useQuery } from "@tanstack/react-query";
import api from "../../../lib/axios";

export type ProductSku = {
  id: number;
  code: string;
  stock_level_id?: number | null;
  quantity_on_hand?: number;
  quantity_reserved?: number;
  stock_reorder_point?: number | null;
};

export type Product = {
  id: number;
  name: string;
  description: string;
  category_name?: string | null;
  supplier_name?: string | null;
  reorder_point: number;
  safety_stock: number;
  skus: ProductSku[];
  unit_price?: number;
  unit_of_measure?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  category_id?: number;
  supplier_id?: number;
};

export type LowStockItem = {
  id: number;
  product_name: string;
  sku_code: string;
  quantity: number;
  reorder_point: number;
  product_id: number;
  reorder_quantity: number;
  supplier_name?: string;
  predicted_stockout_date?: string;
};

export type PaginationMeta = {
  page: number;
  total: number;
  perPage: number;
  next: string | null;
  previous: string | null;
};

const PAGE_SIZE = 20;

const statusParamByLabel: Record<string, string> = {
  "In Stock": "in_stock",
  "Low Stock": "low_stock",
  "Out of Stock": "out_of_stock",
};

const orderingMap: Record<string, string> = {
  sku: 'sku_code',
  product: 'name',
  category: 'category__name',
  qty: 'quantity_on_hand',
  reserved: 'quantity_reserved',
  reorder: 'sku_reorder_point',
  supplier: 'supplier__name',
  status: 'quantity_on_hand',
};

function unwrap<T>(payload: T | { data: T } | { results: T }): T {
  if (payload && typeof payload === "object") {
    if ("data" in payload) return payload.data;
    if ("results" in payload) return payload.results as T;
  }
  return payload as T;
}

function numberFromMeta(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function useInventory(params: {
  search: string;
  statusFilter: string;
  supplierId: string;
  sortField: string;
  sortOrder: string;
  page: number;
  categoryFilter?: string;
}) {
  const ordering = params.sortField
    ? params.sortOrder === "desc"
      ? `-${orderingMap[params.sortField] ?? params.sortField}`
      : (orderingMap[params.sortField] ?? params.sortField)
    : "";
  const orderingParam = ordering ? { ordering } : {};

  const query = useQuery({
    queryKey: [
      "inventory",
      params.search,
      params.statusFilter,
      params.supplierId,
      params.sortField,
      params.sortOrder,
      params.page,
      params.categoryFilter,
    ],
    queryFn: async () => {
      const queryParams: Record<string, unknown> = {
        page: params.page,
        page_size: PAGE_SIZE,
        ...orderingParam,
      };
      if (params.search) queryParams.search = params.search;
      if (params.supplierId) queryParams.supplier = params.supplierId;
      if (params.statusFilter)
        queryParams.stock_status = statusParamByLabel[params.statusFilter];
      if (params.categoryFilter)
        queryParams.category = params.categoryFilter;
      const res = await api.get("/inventory/products/", { params: queryParams });
      const products = unwrap<Product[]>(res.data);
      const meta = res._meta ?? {};

      return {
        products,
        pagination: {
          page: numberFromMeta(meta.page, params.page),
          total: numberFromMeta(meta.total, products.length),
          perPage: numberFromMeta(meta.per_page, PAGE_SIZE),
          next: typeof meta.next === "string" ? meta.next : null,
          previous: typeof meta.previous === "string" ? meta.previous : null,
        } satisfies PaginationMeta,
        lowStock: (res.data as Record<string, unknown>).low_stock as LowStockItem[] ?? [],
      };
    },
  });

  return {
    products: query.data?.products ?? [],
    pagination: query.data?.pagination ?? { page: 1, total: 0, perPage: PAGE_SIZE, next: null, previous: null },
    lowStock: query.data?.lowStock ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    isFetching: query.isFetching,
    refetch: query.refetch,
  };
}
