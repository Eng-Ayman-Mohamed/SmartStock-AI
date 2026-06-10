import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as suppliersApi from '../api';
import type { CreateSupplierPayload, UpdateSupplierPayload } from '../types';

export const suppliersQueryKey = ['suppliers'] as const;

export function useSuppliers() {
  return useQuery({
    queryKey: suppliersQueryKey,
    queryFn: suppliersApi.listSuppliers,
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
