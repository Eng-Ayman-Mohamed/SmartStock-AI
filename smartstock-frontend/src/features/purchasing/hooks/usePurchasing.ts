import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../../store/authStore';
import * as purchasingApi from '../api';

export const purchasingQueryKey = ['purchasing-pending-pos'] as const;

export function usePendingPOs(page = 1, pageSize = 20) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: [...purchasingQueryKey, page, pageSize],
    queryFn: () => purchasingApi.listPendingPOs(page, pageSize),
    enabled: !!token,
    retry: false,
  });
}

export function useApprovePO() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: string }) => purchasingApi.approvePO(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: purchasingQueryKey });
    },
  });
}

export function useRejectPO() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: string }) => purchasingApi.rejectPO(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: purchasingQueryKey });
    },
  });
}

export function useCreatePO() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: purchasingApi.CreatePurchaseOrderPayload) =>
      purchasingApi.createPurchaseOrder(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: purchasingQueryKey });
    },
  });
}

export const poHistoryQueryKey = ['po-history'] as const;

export function usePOHistory(page = 1, pageSize = 20) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: [...poHistoryQueryKey, page, pageSize],
    queryFn: () => purchasingApi.listPOHistory(page, pageSize),
    enabled: !!token,
    retry: false,
  });
}
