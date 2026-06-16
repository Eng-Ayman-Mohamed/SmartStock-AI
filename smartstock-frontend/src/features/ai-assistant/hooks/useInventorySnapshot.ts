import { useQuery } from '@tanstack/react-query';
import { fetchStockSnapshot } from '../api';
import { useAuthStore } from '../../../store/authStore';

export function useInventorySnapshot() {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ['ai-inventory-snapshot'],
    queryFn: fetchStockSnapshot,
    enabled: !!token,
    retry: false,
    staleTime: 60 * 1000,
  });
}