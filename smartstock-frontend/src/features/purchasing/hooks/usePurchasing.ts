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
    onSuccess: async () => {
      await qc.refetchQueries({ queryKey: purchasingQueryKey });
      await qc.refetchQueries({ queryKey: poHistoryQueryKey });
    },
  });
}

export function useRejectPO() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: string }) => purchasingApi.rejectPO(id),
    onSuccess: async () => {
      await qc.refetchQueries({ queryKey: purchasingQueryKey });
      await qc.refetchQueries({ queryKey: poHistoryQueryKey });
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

const poHistoryOrderingMap: Record<string, string> = {
  id: 'id',
  product_name: 'sku__product__name',
  supplier: 'supplier__name',
  quantity: 'quantity',
  total: 'total_cost',
  status: 'status',
  created_at: 'created_at',
  approved_by: 'approved_by__username',
};

export function usePOHistory(
  page = 1,
  pageSize = 20,
  sortField?: string,
  sortOrder?: string,
  searchQuery?: string,
) {
  const token = useAuthStore((s) => s.token);
  const ordering = sortField
    ? sortOrder === 'desc'
      ? `-${poHistoryOrderingMap[sortField] ?? sortField}`
      : (poHistoryOrderingMap[sortField] ?? sortField)
    : '';
  return useQuery({
    queryKey: [...poHistoryQueryKey, page, pageSize, sortField, sortOrder, searchQuery],
    queryFn: () => purchasingApi.listPOHistory(page, pageSize, ordering, searchQuery),
    enabled: !!token,
    retry: false,
  });
}
