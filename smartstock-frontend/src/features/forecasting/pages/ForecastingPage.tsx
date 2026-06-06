import { useState } from 'react';
import { RefreshCw, TrendingUp } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useForecastDashboard } from '../hooks/useForecastDashboard';
import SkuChart from '../components/SkuChart';
import AlertBanner, { classifyAlert } from '../components/AlertBanner';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';

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
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-page-heading text-gray-900">Demand Forecasting</h1>
          <p className="text-body text-gray-600 mt-1">AI-powered 30-day demand predictions per SKU</p>
        </div>
        <Button variant="primary" size="md" onClick={handleRefresh}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </div>

      {alerts.length > 0 && (
        <Card title="Alerts" subtitle={`${alerts.length} items need attention`}>
          <div className="space-y-2">
            {alerts.sort((a) => a!.severity === 'critical' ? -1 : 1).map(alert =>
              <AlertBanner key={alert!.sku.id} alert={alert!} onDismiss={handleDismiss} />
            )}
          </div>
        </Card>
      )}

      {isError && (
        <div className="rounded-md border-[0.5px] border-red-200 bg-red-50 px-4 py-3 text-body text-red-800">
          Failed to load forecast data from /api/forecasting/dashboard/
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
          {[1,2,3,4].map(i => (
            <div key={i} className="h-72 rounded-md border-[0.5px] border-gray-100 bg-gray-100 animate-skeleton" />
          ))}
        </div>
      ) : skus.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center justify-center py-16">
            <TrendingUp className="w-12 h-12 text-gray-300 mb-4" />
            <h3 className="text-card-title text-gray-700 mb-1">No forecast data</h3>
            <p className="text-body text-gray-500 text-center max-w-[280px]">
              Forecast data will appear here once the AI model completes its initial analysis.
            </p>
          </div>
        </Card>
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
