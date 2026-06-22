import { Bell, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Skeleton from '../../../shared/components/Skeleton';
import { useMonitoringBanners } from '../hooks/useMonitoringBanners';
import type { MonitoringBanner } from '../hooks/useMonitoringBanners';
import api from '../../../lib/axios';
import { useQueryClient } from '@tanstack/react-query';
import { useToastStore } from '../../../store/toastStore';

const levelConfig: Record<MonitoringBanner['level'], { icon: typeof Bell; color: string }> = {
  error: { icon: AlertCircle, color: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:border-red-800 dark:text-red-300' },
  warning: { icon: AlertTriangle, color: 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:border-orange-800 dark:text-orange-300' },
  info: { icon: Info, color: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-300' },
};

function BannerItem({ banner }: { banner: MonitoringBanner }) {
  const qc = useQueryClient();
  const addToast = useToastStore((s) => s.addToast);
  const config = levelConfig[banner.level] ?? levelConfig.info;
  const Icon = config.icon;

  const handleDismiss = async () => {
    try {
      await api.post(`/monitoring/banners/${banner.id}/dismiss/`);
      qc.invalidateQueries({ queryKey: ['monitoring-banners'] });
      addToast('Banner dismissed', 'success');
    } catch {
      addToast('Failed to dismiss banner', 'error');
    }
  };

  return (
    <div className={`flex items-start gap-3 p-3 rounded-md border ${config.color}`}>
      <Icon className="w-4 h-4 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-body font-medium">{banner.title}</p>
        <p className="text-caption mt-0.5 opacity-80">{banner.message}</p>
      </div>
      <button
        onClick={handleDismiss}
        className="shrink-0 p-1 rounded hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
        title="Dismiss"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

export default function MonitoringBanners() {
  const { data: banners, isLoading, error } = useMonitoringBanners();

  if (isLoading) {
    return <Skeleton className="h-16" />;
  }

  if (error || !banners || banners.length === 0) {
    return null;
  }

  return (
    <Card title="System Alerts" subtitle={`${banners.length} active alert${banners.length !== 1 ? 's' : ''}`}>
      <div className="space-y-2 max-h-[240px] overflow-y-auto overscroll-contain">
        {banners.map((banner) => (
          <BannerItem key={banner.id} banner={banner} />
        ))}
      </div>
    </Card>
  );
}
