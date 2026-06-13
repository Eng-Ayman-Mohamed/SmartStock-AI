import api from '../../lib/axios';
import type { Supplier, CreateSupplierPayload, UpdateSupplierPayload, PendingPO } from './types';

export async function listSuppliers(searchQuery?: string): Promise<Supplier[]> {
  const params = searchQuery ? { search: searchQuery } : {};
  const { data } = await api.get<{ status: string; data: Supplier[] }>('/purchasing/suppliers/', { params });
  return data.data ?? data;
}

export async function createSupplier(payload: CreateSupplierPayload): Promise<Supplier> {
  const { data } = await api.post<{ status: string; data: Supplier }>('/purchasing/suppliers/', payload);
  return data.data ?? data;
}

export async function updateSupplier(id: number, payload: UpdateSupplierPayload): Promise<Supplier> {
  const { data } = await api.patch<{ status: string; data: Supplier }>(`/purchasing/suppliers/${id}/`, payload);
  return data.data ?? data;
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
  const { data } = await api.get<{ status: string; data: RawPO[] }>(
    '/purchasing/orders/',
    { params: { status: 'pending_approval', page_size: 100 } }
  );
  const items = data.data ?? [];
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
