import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../../store/authStore';
import * as suppliersApi from '../api';
import type { CreateSupplierPayload, UpdateSupplierPayload } from '../types';

export const suppliersQueryKey = ['suppliers'] as const;

const orderingMap: Record<string, string> = {
  name: 'name',
  contact_email: 'contact_email',
  default_lead_time_days: 'default_lead_time_days',
  is_active: 'is_active',
};

export function useSuppliers(
  searchQuery?: string,
  page: number = 1,
  pageSize: number = 20,
  sortField?: string,
  sortOrder?: string,
) {
  const token = useAuthStore((s) => s.token);
  const ordering = sortField
    ? sortOrder === 'desc'
      ? `-${orderingMap[sortField] ?? sortField}`
      : (orderingMap[sortField] ?? sortField)
    : '';
  return useQuery({
    queryKey: [...suppliersQueryKey, page, pageSize, searchQuery, sortField, sortOrder],
    queryFn: () => suppliersApi.listSuppliers(searchQuery, page, pageSize, ordering),
    enabled: !!token,
    retry: false,
  });
}

export function useCreateSupplier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateSupplierPayload) => suppliersApi.createSupplier(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: suppliersQueryKey });
    },
  });
}

export function useUpdateSupplier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateSupplierPayload }) =>
      suppliersApi.updateSupplier(id, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: suppliersQueryKey });
    },
  });
}

export function useDeleteSupplier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => suppliersApi.deleteSupplier(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: suppliersQueryKey });
    },
  });
}
