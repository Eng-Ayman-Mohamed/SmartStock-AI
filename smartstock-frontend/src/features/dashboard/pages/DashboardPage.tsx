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
import { Package, AlertTriangle, ShoppingCart, TrendingUp } from 'lucide-react';
import { useReorderAlerts } from '../hooks/useReorderAlerts';
import { usePendingPOs } from '../hooks/usePendingPOs';
import ReorderAlertList from '../components/ReorderAlertList';
import AgentRunStatus from '../components/AgentRunStatus';
import PendingPOQueue from '../components/PendingPOQueue';
import SupplierWarningBadge from '../components/SupplierWarningBadge';

const chartData = [
  { date: '01 Jun', demand: 120, actual: 115, upper: 140, lower: 100 },
  { date: '05 Jun', demand: 145, actual: 138, upper: 170, lower: 120 },
  { date: '10 Jun', demand: 130, actual: null, upper: 160, lower: 105 },
  { date: '15 Jun', demand: 160, actual: null, upper: 190, lower: 130 },
  { date: '20 Jun', demand: 150, actual: null, upper: 180, lower: 120 },
  { date: '25 Jun', demand: 175, actual: null, upper: 205, lower: 145 },
  { date: '30 Jun', demand: 165, actual: null, upper: 195, lower: 135 },
];

function ForecastChart() {
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

export default function DashboardPage() {
  const { data: alerts } = useReorderAlerts();
  const { data: pendingPOs } = usePendingPOs();

  const lowStockCount = alerts?.length ?? 0;
  const pendingPOCount = pendingPOs?.length ?? 0;

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-page-heading text-ink">Dashboard</h1>
        <p className="text-body text-ink-muted mt-1">
          {pendingPOCount > 0
            ? `You have ${pendingPOCount} pending PO${pendingPOCount > 1 ? 's' : ''}.`
            : 'All purchase orders are up to date.'}
        </p>
      </div>

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
          <ForecastChart />
        </Card>

        <ReorderAlertList />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PendingPOQueue />
        <AgentRunStatus />
      </div>
    </div>
  );
}
