import api from '../../lib/axios';
import type { Supplier, CreateSupplierPayload, UpdateSupplierPayload, PendingPO } from './types';

export async function listSuppliers(searchQuery?: string): Promise<Supplier[]> {
  const params = searchQuery ? { search: searchQuery } : {};
  const { data } = await api.get<Supplier[]>('/purchasing/suppliers/', { params });
  return data;
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

export async function listPendingPOs(): Promise<PendingPO[]> {
  const { data } = await api.get<RawPO[]>(
    '/purchasing/orders/',
    { params: { status: 'pending_approval', page_size: 100 } }
  );
  const items = data ?? [];
  return items.map((item) => {
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
  });
}

export async function approvePO(id: string): Promise<void> {
  const numericId = id.replace('PO-', '');
  await api.post(`/purchasing/orders/${numericId}/approve/`);
}

export async function rejectPO(id: string): Promise<void> {
  const numericId = id.replace('PO-', '');
  await api.post(`/purchasing/orders/${numericId}/reject/`);
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

export async function listPOHistory(): Promise<POHistoryItem[]> {
  const { data } = await api.get<POHistoryRaw[]>('/purchasing/orders/', {
    params: { page_size: 100 },
  });
  const items = data ?? [];
  return items
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
    }));
}
