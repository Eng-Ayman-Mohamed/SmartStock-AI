import { useQuery } from '@tanstack/react-query';
import { fetchSKUCount } from '../api';
import { useAuthStore } from '../../../store/authStore';

export function useSKUCount() {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ['sku-count'],
    queryFn: fetchSKUCount,
    enabled: !!token,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}