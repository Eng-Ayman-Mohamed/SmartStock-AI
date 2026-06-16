import { useQuery } from '@tanstack/react-query';
import api from '../../lib/axios';

async function checkHealth(): Promise<boolean> {
  try {
    await api.get('/health/live/');
    return true;
  } catch {
    return false;
  }
}

export function useServerHealth() {
  return useQuery({
    queryKey: ['server-health'],
    queryFn: checkHealth,
    retry: false,
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
}