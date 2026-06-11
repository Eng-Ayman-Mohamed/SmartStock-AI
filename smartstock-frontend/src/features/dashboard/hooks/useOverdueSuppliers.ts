import { useQuery } from '@tanstack/react-query';
import { fetchOverdueSuppliers } from '../api';
import type { OverdueSupplier } from '../types';

export function useOverdueSuppliers() {
  return useQuery<OverdueSupplier[]>({
    queryKey: ['overdue-suppliers'],
    queryFn: fetchOverdueSuppliers,
    refetchInterval: 60_000,
  });
}
