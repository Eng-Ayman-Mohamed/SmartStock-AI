import api from '../../lib/axios';
import type { Supplier, CreateSupplierPayload, UpdateSupplierPayload, PendingPO } from './types';

export async function listSuppliers(searchQuery?: string): Promise<Supplier[]> {
  const params = searchQuery ? { search: searchQuery } : {};
  const { data } = await api.get<Supplier[]>('/inventory/suppliers/', { params });
  return data;
}

export async function createSupplier(payload: CreateSupplierPayload): Promise<Supplier> {
  const { data } = await api.post<Supplier>('/inventory/suppliers/', payload);
  return data;
}

export async function updateSupplier(id: number, payload: UpdateSupplierPayload): Promise<Supplier> {
  const { data } = await api.patch<Supplier>(`/inventory/suppliers/${id}/`, payload);
  return data;
}

export async function deleteSupplier(id: number): Promise<void> {
  await api.delete(`/inventory/suppliers/${id}/`);
}

export async function listPendingPOs(): Promise<PendingPO[]> {
  const { data } = await api.get<PendingPO[]>('/purchasing/purchase-orders/pending/');
  return data;
}

export async function approvePO(id: string, approvedQty: number): Promise<void> {
  const { data } = await api.patch(`/purchasing/purchase-orders/${id}/approve/`, { approved_qty: approvedQty });
  return data;
}

export async function rejectPO(id: string, reason?: string): Promise<void> {
  const { data } = await api.patch(`/purchasing/purchase-orders/${id}/reject/`, { reason: reason || '' });
  return data;
}
