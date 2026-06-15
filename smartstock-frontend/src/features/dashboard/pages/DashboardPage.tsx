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
import { Package, AlertTriangle, ShoppingCart, TrendingUp, RefreshCw, AlertCircle } from 'lucide-react';
import { useReorderAlerts } from '../hooks/useReorderAlerts';
import { usePendingPOs } from '../hooks/usePendingPOs';
import { useAgentRuns } from '../hooks/useAgentRuns';
import { useForecastDashboard } from '../../forecasting/hooks/useForecastDashboard';
import ReorderAlertList from '../components/ReorderAlertList';
import AgentRunStatus from '../components/AgentRunStatus';
import PendingPOQueue from '../components/PendingPOQueue';
import SupplierWarningBadge from '../components/SupplierWarningBadge';

interface ChartPoint {
  date: string;
  demand: number;
  actual: number | null;
  upper: number;
  lower: number;
}

function ForecastChart({ data: allSkus }: { data: ChartPoint[] | null }) {
  const chartData = allSkus ?? [];
  return (
    <div className="h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
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
          <ReferenceLine
            y={150}
            stroke="var(--color-orange-600)"
            strokeWidth={1.5}
            strokeDasharray="6 4"
            label={{
              value: 'Reorder point',
              position: 'insideTopRight',
              fontSize: 11,
              fill: 'var(--color-orange-600)',
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-4 mt-2 text-caption text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-brand-600" /> Predicted demand
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5" style={{ borderTop: '1.5px dashed var(--color-ink-secondary)', height: 0 }} /> Actual sales
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-[9px] bg-brand-50 border-[0.5px] border-brand-100" /> Confidence interval
        </span>
      </div>
    </div>
  );
}

function isAgentPipelineStale(runs: { created_at: string }[] | undefined): boolean {
  if (!runs || runs.length === 0) return true;
  const now = new Date();
  const mostRecent = new Date(runs[0].created_at);
  const diffMs = now.getTime() - mostRecent.getTime();
  const STALE_THRESHOLD_MS = 25 * 60 * 60 * 1000;
  return diffMs >= STALE_THRESHOLD_MS;
}

export default function DashboardPage() {
  const qc = useQueryClient();
  const { data: alerts } = useReorderAlerts();
  const { data: pendingPOs } = usePendingPOs();
  const { data: forecastData } = useForecastDashboard();
  const { data: agentRuns } = useAgentRuns();

  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    await Promise.all([
      qc.invalidateQueries({ queryKey: ['reorder-alerts'] }),
      qc.invalidateQueries({ queryKey: ['agent-runs'] }),
      qc.invalidateQueries({ queryKey: ['pending-pos'] }),
    ]);
    setIsRefreshing(false);
  }, [qc, isRefreshing]);

  const lowStockCount = alerts?.length ?? 0;
  const pendingPOCount = pendingPOs?.length ?? 0;
  const agentStale = isAgentPipelineStale(agentRuns);

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
      <div className="flex items-start justify-between">
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
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-ink-secondary bg-white border border-hairline rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {agentStale && (
        <div className="flex items-center gap-3 px-4 py-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p className="text-body">Agent pipeline may not be running.</p>
        </div>
      )}

      <SupplierWarningBadge />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard label="Total SKUs" value="1,247" icon={Package} />
        <StatCard
          label="Low Stock Alerts"
          value={String(lowStockCount)}
          accent="orange"
          icon={AlertTriangle}
          trend={lowStockCount > 0 ? { direction: 'up', percentage: `${lowStockCount}`, color: 'text-orange-600' } : undefined}
        />
        <StatCard label="Pending POs" value={String(pendingPOCount)} accent="orange" icon={ShoppingCart} />
        <StatCard label="Forecast Accuracy" value="87.4%" accent="purple" icon={TrendingUp} trend={{ direction: 'up', percentage: '2.1%' }} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
        <Card title="30-Day Demand Forecast">
          <ForecastChart data={chartData} />
        </Card>

        <ReorderAlertList onRefresh={handleRefresh} isRefreshing={isRefreshing} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PendingPOQueue />
        <AgentRunStatus />
      </div>
    </div>
  );
}
