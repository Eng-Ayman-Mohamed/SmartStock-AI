import { useState } from 'react';
import { TrendingUp, RefreshCw } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useForecastDashboard } from '../hooks/useForecastDashboard';
import SkuChart from '../components/SkuChart';
import AlertBanner, { classifyAlert } from '../components/AlertBanner';

export default function ForecastingPage() {
  const { data, isLoading, isError } = useForecastDashboard();
  const queryClient = useQueryClient();
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const skus = data?.skus ?? [];
  const alerts = skus
    .map(classifyAlert)
    .filter(Boolean)
    .filter(a => !dismissed.has(a!.sku.id)) as ReturnType<typeof classifyAlert>[];

  const handleDismiss = (id: string) =>
    setDismissed(prev => new Set([...prev, id]));

  const handleRefresh = () =>
    queryClient.invalidateQueries({ queryKey: ['forecast-dashboard'] });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-surface-100">Demand Forecasting</h2>
          <p className="text-sm text-surface-400 mt-1">
            AI-powered 30-day demand predictions per SKU
          </p>
        </div>
        <button onClick={handleRefresh}
          className="flex items-center gap-2 h-9 px-4 rounded-lg bg-gradient-to-r
            from-emerald-600 to-emerald-500 text-sm font-medium text-white
            shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 transition-all">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.sort((a, b) => a!.severity === 'critical' ? -1 : 1).map(alert =>
            <AlertBanner key={alert!.sku.id} alert={alert!} onDismiss={handleDismiss} />
          )}
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-danger/30 bg-danger/10
          px-4 py-3 text-sm text-danger">
          Failed to load forecast data from /api/forecasting/dashboard/
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
          {[1,2,3,4].map(i => (
            <div key={i} className="h-72 rounded-2xl border border-surface-800/50
              bg-surface-900/60 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
          {skus.map((sku, i) => (
            <SkuChart key={sku.id} sku={sku} colorIdx={i}
              hasAlert={alerts.some(a => a!.sku.id === sku.id)} />
          ))}
        </div>
      )}
    </div>
  );
}