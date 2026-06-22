import api from '../../lib/axios';
import type { Supplier, CreateSupplierPayload, UpdateSupplierPayload, PendingPO } from './types';

export interface SKUOption {
  id: number;
  code: string;
  product_name: string;
}

export async function listSKUOptions(searchQuery?: string): Promise<SKUOption[]> {
  const params: Record<string, string | number | undefined> = {
    search: searchQuery || undefined,
  };
  const { data } = await api.get<SKUOption[]>('/inventory/skus/', { params });
  return data;
}

export interface SupplierOption {
  id: number;
  name: string;
}

export async function listSupplierOptions(searchQuery?: string): Promise<SupplierOption[]> {
  const params: Record<string, string | number | undefined> = {
    search: searchQuery || undefined,
  };
  const { data } = await api.get<SupplierOption[]>('/purchasing/suppliers/', { params });
  return data;
}

export async function listSuppliers(
  searchQuery?: string,
  page: number = 1,
  pageSize: number = 20,
  ordering?: string,
): Promise<PaginatedResponse<Supplier>> {
  const params: Record<string, string | number | undefined> = {
    page,
    page_size: pageSize,
    search: searchQuery || undefined,
    ordering: ordering || undefined,
  };
  const res = await api.get<Supplier[]>('/purchasing/suppliers/', { params });
  return {
    results: res.data,
    count: res._meta?.total as number ?? 0,
    next: null,
    previous: null,
  };
}

export async function createSupplier(payload: CreateSupplierPayload): Promise<Supplier> {
  const { data } = await api.post<Supplier>('/purchasing/suppliers/', payload);
  return data;
}

export async function updateSupplier(id: number, payload: UpdateSupplierPayload): Promise<Supplier> {
  const { data } = await api.patch<Supplier>(`/purchasing/suppliers/${id}/`, payload);
  return data;
}

export async function deleteSupplier(id: number): Promise<void> {
  await api.delete(`/purchasing/suppliers/${id}/`);
}

interface RawPO {
  id: number;
  sku_code: string;
  product_name: string;
  supplier_name: string;
  quantity: number;
  total_cost: string;
  status: string;
  agent_reasoning: string | null;
  [key: string]: unknown;
}

export async function listPendingPOs(page = 1, pageSize = 20): Promise<PaginatedResponse<PendingPO>> {
  const res = await api.get<RawPO[]>('/purchasing/orders/', {
    params: { status: 'pending_approval', page, page_size: pageSize },
  });
  return {
    results: (res.data ?? []).map((item) => {
      const total = parseFloat(item.total_cost) || 0;
      const qty = item.quantity || 1;
      return {
        id: `PO-${item.id}`,
        product: item.product_name,
        sku: item.sku_code,
        supplier: item.supplier_name,
        predicted_stockout: 'N/A',
        recommended_qty: qty,
        unit_cost: Math.round((total / qty) * 100) / 100,
        estimated_total_cost: `$${total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        agent_reasoning: item.agent_reasoning,
      };
    }),
    count: res._meta?.total as number ?? 0,
    next: null,
    previous: null,
  };
}

export async function approvePO(id: string): Promise<void> {
  const numericId = id.replace('PO-', '');
  await api.post(`/purchasing/orders/${numericId}/approve/`);
}

export async function rejectPO(id: string): Promise<void> {
  const numericId = id.replace('PO-', '');
  await api.post(`/purchasing/orders/${numericId}/reject/`);
}

export interface CreatePurchaseOrderPayload {
  sku: number;
  supplier: number;
  quantity: number;
  total_cost: number;
  notes?: string;
  agent_reasoning?: string;
}

export async function createPurchaseOrder(
  payload: CreatePurchaseOrderPayload,
): Promise<PendingPO> {
  const { data } = await api.post<PendingPO>('/purchasing/orders/', payload);
  return data;
}

interface POHistoryRaw {
  id: number;
  product_name: string;
  supplier_name: string;
  quantity: number;
  total_cost: string;
  status: string;
  created_at: string;
  approved_by_name: string | null;
}

export interface POHistoryItem {
  id: string;
  product_name: string;
  supplier: string;
  quantity: number;
  total: string;
  status: string;
  created_at: string;
  approved_by: string;
}

function formatPODate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatTotal(cost: string): string {
  const num = parseFloat(cost) || 0;
  return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export async function listPOHistory(
  page = 1,
  pageSize = 20,
  ordering?: string,
): Promise<PaginatedResponse<POHistoryItem>> {
  const params: Record<string, string | number | undefined> = {
    page,
    page_size: pageSize,
    ordering: ordering || undefined,
  };
  const res = await api.get<POHistoryRaw[]>('/purchasing/orders/', { params });
  return {
    results: (res.data ?? [])
      .filter((item) => item.status !== 'pending_approval' && item.status !== 'draft')
      .map((item) => ({
        id: `PO-${item.id}`,
        product_name: item.product_name,
        supplier: item.supplier_name,
        quantity: item.quantity,
        total: formatTotal(item.total_cost),
        status: item.status,
        created_at: formatPODate(item.created_at),
        approved_by: item.approved_by_name ?? '—',
      })),
    count: res._meta?.total as number ?? 0,
    next: null,
    previous: null,
  };
}
