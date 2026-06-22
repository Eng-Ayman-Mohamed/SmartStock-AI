import { useQuery } from '@tanstack/react-query';
import api from '../../../lib/axios';
import { useAuthStore } from '../../../store/authStore';

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  database: 'ok' | 'error';
  redis: 'ok' | 'error';
  celery: 'ok' | 'error';
  storage: 'ok' | 'error';
  agents: 'ok' | 'error';
  stale_running_runs: number;
}

export function useHealthStatus() {
  const token = useAuthStore((s) => s.token);
  return useQuery<HealthStatus>({
    queryKey: ['health-full'],
    queryFn: async () => {
      const { data } = await api.get('/health/full/');
      return (data.data ?? data) as HealthStatus;
    },
    enabled: !!token,
    refetchInterval: 60_000,
    retry: false,
  });
}
