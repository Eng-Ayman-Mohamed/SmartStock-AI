import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../../store/authStore';
import * as purchasingApi from '../api';

export const purchasingQueryKey = ['pending-pos'] as const;

export function usePendingPOs() {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: purchasingQueryKey,
    queryFn: () => purchasingApi.listPendingPOs(),
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
