import { useQuery } from '@tanstack/react-query';
import { fetchLowStockItems } from '../api';
import { useAuthStore } from '../../../store/authStore';
import type { ReorderAlert } from '../types';

export function useReorderAlerts() {
  const token = useAuthStore((s) => s.token);
  return useQuery<ReorderAlert[]>({
    queryKey: ['reorder-alerts'],
    queryFn: fetchLowStockItems,
    refetchInterval: 30_000,
    enabled: !!token,
    retry: false,
  });
}
