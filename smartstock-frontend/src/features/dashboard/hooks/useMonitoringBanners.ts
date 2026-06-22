import { useQuery } from '@tanstack/react-query';
import api from '../../../lib/axios';
import { useAuthStore } from '../../../store/authStore';

export interface MonitoringBanner {
  id: number;
  title: string;
  message: string;
  level: 'info' | 'warning' | 'error';
  created_at: string | null;
}

export function useMonitoringBanners() {
  const token = useAuthStore((s) => s.token);
  return useQuery<MonitoringBanner[]>({
    queryKey: ['monitoring-banners'],
    queryFn: async () => {
      const { data } = await api.get('/monitoring/banners/');
      return (data.data ?? data) as MonitoringBanner[];
    },
    enabled: !!token,
    refetchInterval: 120_000,
    retry: false,
  });
}
