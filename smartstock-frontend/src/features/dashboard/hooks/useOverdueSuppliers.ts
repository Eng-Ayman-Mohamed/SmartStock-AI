import { useQuery } from '@tanstack/react-query';
import { fetchOverdueSuppliers } from '../api';
import { useAuthStore } from '../../../store/authStore';
import type { OverdueSupplier } from '../types';

export function useOverdueSuppliers() {
  const token = useAuthStore((s) => s.token);
  return useQuery<OverdueSupplier[]>({
    queryKey: ['overdue-suppliers'],
    queryFn: fetchOverdueSuppliers,
    refetchInterval: 60_000,
    enabled: !!token,
    retry: false,
  });
}
