import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as purchasingApi from '../api';

export const purchasingQueryKey = ['pending-orders'] as const;

export function usePendingPOs() {
  return useQuery({
    queryKey: purchasingQueryKey,
    queryFn: () => purchasingApi.listPendingPOs(),
  });
}

export function useApprovePO() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, qty }: { id: string; qty: number }) => purchasingApi.approvePO(id, qty),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: purchasingQueryKey });
    },
  });
}

export function useRejectPO() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => purchasingApi.rejectPO(id, reason),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: purchasingQueryKey });
    },
  });
}
