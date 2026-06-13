import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { approvePO, fetchPendingPOs, rejectPO } from '../api';
import { useAuthStore } from '../../../store/authStore';
import type { PurchaseOrder } from '../types';

export function usePendingPOs() {
  const token = useAuthStore((s) => s.token);
  return useQuery<PurchaseOrder[]>({
    queryKey: ['pending-pos'],
    queryFn: fetchPendingPOs,
    refetchInterval: 30_000,
    enabled: !!token,
    retry: false,
  });
}

export function useApprovePO() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (poId: number) => approvePO(poId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pending-pos'] });
    },
  });
}

export function useRejectPO() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (poId: number) => rejectPO(poId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pending-pos'] });
    },
  });
}
