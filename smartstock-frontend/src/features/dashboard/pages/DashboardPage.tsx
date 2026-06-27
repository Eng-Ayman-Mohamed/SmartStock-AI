import { useCallback, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import StatCard from '../../../shared/components/StatCard';
import Card from '../../../shared/components/Card';
import Skeleton from '../../../shared/components/Skeleton';
import { Package, AlertTriangle, ShoppingCart, TrendingUp, RefreshCw, AlertCircle } from 'lucide-react';
import { useReorderAlerts } from '../hooks/useReorderAlerts';
import { usePendingPOs } from '../hooks/usePendingPOs';
import { useSKUCount } from '../hooks/useSKUCount';
import { useForecastDashboard } from '../../forecasting/hooks/useForecastDashboard';
import ReorderAlertList from '../components/ReorderAlertList';
import PendingPOQueue from '../components/PendingPOQueue';
import SystemHealth from '../components/SystemHealth';

interface ChartPoint {
  date: string;
  demand: number;
  actual: number | null;
  upper: number;
  lower: number;
}

function ForecastChart({ data, reorderPoint }: { data: ChartPoint[] | null; reorderPoint?: number | null }) {
  if (!data || data.length === 0) {
    return <div className="h-[clamp(200px,32vh,400px)] flex items-center justify-center text-body text-ink-muted">No forecast data available</div>;
  }
  return (
    <div className="h-[clamp(200px,32vh,400px)]">
      <ResponsiveContainer width="100%" height="100%" minHeight={200}>
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
           <CartesianGrid strokeDasharray="3 3" stroke="var(--color-hairline)" horizontal={true} vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12, fill: 'var(--color-ink-faint)' }}
            tickLine={false}
            axisLine={{ stroke: 'var(--color-hairline)', strokeWidth: 0.5 }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: 'var(--color-ink-faint)' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-canvas)',
              border: '1px solid var(--color-hairline)',
              borderRadius: '8px',
              boxShadow: 'var(--shadow-soft)',
              fontSize: '14px',
            }}
            labelStyle={{ fontSize: '12px', color: 'var(--color-ink-faint)' }}
          />
          <Area
            type="monotone"
            dataKey="upper"
            stroke="var(--color-brand-100)"
            strokeWidth={1}
            strokeDasharray="4 4"
            fill="var(--color-brand-50)"
            fillOpacity={0.4}
            dot={false}
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="var(--color-brand-100)"
            strokeWidth={1}
            strokeDasharray="4 4"
            fill="none"
            dot={false}
          />
          <Area
            type="monotone"
            dataKey="demand"
            stroke="var(--color-brand-600)"
            strokeWidth={2}
            fill="none"
            dot={false}
            activeDot={{ r: 4, fill: 'var(--color-brand-600)' }}
          />
          <Area
            type="monotone"
            dataKey="actual"
            stroke="var(--color-ink-secondary)"
            strokeWidth={1.5}
            strokeDasharray="6 4"
            fill="none"
            dot={false}
            connectNulls={false}
          />
          {reorderPoint != null && reorderPoint > 0 && (
            <ReferenceLine
              y={reorderPoint}
              stroke="var(--color-orange-600)"
              strokeWidth={1.5}
              strokeDasharray="6 4"
              label={{
                value: `Reorder (${reorderPoint})`,
                position: 'insideTopRight',
                fontSize: 11,
                fill: 'var(--color-orange-600)',
              }}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap items-center gap-4 mt-2 text-caption text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-brand-600" /> Predicted demand
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5" style={{ borderTop: '1.5px dashed var(--color-ink-secondary)', height: 0 }} /> Actual sales
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-[9px] bg-brand-50 border-[0.5px] border-brand-100 dark:bg-brand-900/30 dark:border-brand-800" /> Confidence interval
        </span>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const qc = useQueryClient();
  const { data: alerts, isLoading: alertsLoading, isError: alertsError } = useReorderAlerts();
  const { data: pendingPOs, isLoading: pendingLoading, isError: pendingError } = usePendingPOs();
  const { data: forecastData, isLoading: forecastLoading, isError: forecastError } = useForecastDashboard();
  const { data: skuCount, isLoading: skuLoading, isError: skuError } = useSKUCount();

  const [isRefreshing, setIsRefreshing] = useState(false);

  const isError = alertsError || pendingError || forecastError || skuError;

  const handleRefresh = useCallback(async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    await Promise.all([
      qc.invalidateQueries({ queryKey: ['reorder-alerts'] }),
      qc.invalidateQueries({ queryKey: ['pending-pos'] }),
      qc.invalidateQueries({ queryKey: ['po-history'] }),
      qc.invalidateQueries({ queryKey: ['forecast-dashboard'] }),
      qc.invalidateQueries({ queryKey: ['overdue-suppliers'] }),
      qc.invalidateQueries({ queryKey: ['sku-count'] }),
      qc.invalidateQueries({ queryKey: ['health-full'] }),
    ]);
    setIsRefreshing(false);
  }, [qc, isRefreshing]);

  const lowStockCount = alerts?.length ?? 0;
  const pendingPOCount = pendingPOs?.length ?? 0;

  const forecastAccuracy = useMemo(() => {
    if (!forecastData?.skus?.length) return null;
    const scores = forecastData.skus
      .filter((s) => s.confidence_score > 0)
      .map((s) => s.confidence_score);
    if (scores.length === 0) return null;
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
    return { value: `${avg.toFixed(1)}%` };
  }, [forecastData]);

  const avgReorderPoint = useMemo(() => {
    if (!forecastData?.skus?.length) return null;
    const points = forecastData.skus.map((s) => s.reorder_point).filter((p) => p > 0);
    if (points.length === 0) return null;
    return Math.round(points.reduce((a, b) => a + b, 0) / points.length);
  }, [forecastData]);

  const chartData = useMemo(() => {
    if (!forecastData?.skus?.length) return null;
    const dateMap = new Map<string, { demand: number; upper: number; lower: number }>();
    for (const sku of forecastData.skus) {
      for (const day of sku.forecast ?? []) {
        const existing = dateMap.get(day.date) ?? { demand: 0, upper: 0, lower: 0 };
        existing.demand += day.demand;
        existing.upper = Math.max(existing.upper, day.upper_bound ?? 0);
        existing.lower = existing.lower === 0
          ? (day.lower_bound ?? 0)
          : Math.min(existing.lower, day.lower_bound ?? 0);
        dateMap.set(day.date, existing);
      }
    }
    return Array.from(dateMap.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, vals]) => ({
        date: new Date(date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
        demand: Math.round(vals.demand),
        actual: null,
        upper: Math.round(vals.upper),
        lower: Math.round(vals.lower),
      } satisfies ChartPoint));
  }, [forecastData]);

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-page-heading text-ink">Dashboard</h1>
          <p className="text-body text-ink-muted mt-1">
            {pendingPOCount > 0
              ? `You have ${pendingPOCount} pending PO${pendingPOCount > 1 ? 's' : ''}.`
              : 'All purchase orders are up to date.'}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="inline-flex items-center gap-2 h-9 px-4 text-body font-medium text-ink-secondary bg-canvas border border-hairline rounded-full hover:bg-canvas-soft disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {isError && (
        <div className="flex items-center gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-800 dark:bg-red-900/30 dark:border-red-800 dark:text-red-200">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p className="text-body flex-1">Failed to load dashboard data.</p>
          <button onClick={handleRefresh} className="text-caption font-medium text-red-700 dark:text-red-300 hover:underline">Retry</button>
        </div>
      )}

      <SystemHealth />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {skuLoading ? (
          <Skeleton className="h-24" />
        ) : (
          <StatCard label="Total SKUs" value={String(skuCount ?? 0)} icon={Package} />
        )}
        {alertsLoading ? (
          <Skeleton className="h-24" />
        ) : (
          <StatCard
            label="Low Stock Alerts"
            value={String(lowStockCount)}
            accent="orange"
            icon={AlertTriangle}
            trend={lowStockCount > 0 ? { direction: 'up', percentage: `${lowStockCount}`, color: 'text-orange-600' } : undefined}
          />
        )}
        {pendingLoading ? (
          <Skeleton className="h-24" />
        ) : (
          <StatCard label="Pending POs" value={String(pendingPOCount)} accent="orange" icon={ShoppingCart} />
        )}
        {forecastLoading ? (
          <Skeleton className="h-24" />
        ) : (
          <StatCard label="Forecast Accuracy" value={forecastAccuracy?.value ?? 'N/A'} accent="purple" icon={TrendingUp} />
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
        <Card title="30-Day Demand Forecast">
          <ForecastChart data={chartData} reorderPoint={avgReorderPoint} />
        </Card>

        <ReorderAlertList onRefresh={handleRefresh} isRefreshing={isRefreshing} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PendingPOQueue />
      </div>
    </div>
  );
}
