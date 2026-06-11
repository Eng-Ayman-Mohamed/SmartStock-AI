import { useQuery } from '@tanstack/react-query';
import { fetchLowStockItems } from '../api';
import type { ReorderAlert } from '../types';

export function useReorderAlerts() {
  return useQuery<ReorderAlert[]>({
    queryKey: ['reorder-alerts'],
    queryFn: fetchLowStockItems,
    refetchInterval: 30_000,
  });
}
