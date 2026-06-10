import api from '../../lib/axios';
import type { Supplier, CreateSupplierPayload, UpdateSupplierPayload } from './types';

export async function listSuppliers(): Promise<Supplier[]> {
  const { data } = await api.get<Supplier[]>('/inventory/suppliers/');
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
