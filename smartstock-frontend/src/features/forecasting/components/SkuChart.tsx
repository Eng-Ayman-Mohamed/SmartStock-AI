import { TrendingUp, AlertTriangle } from 'lucide-react';
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
import type { SkuForecast, ForecastDay } from '../hooks/useForecastDashboard';

const COLORS = ['#185FA5', '#3B6D11', '#854F0B', '#A32D2D', '#378ADD', '#534AB7', '#D14545', '#2675C9'];

interface SkuChartProps {
  sku: SkuForecast;
  colorIdx: number;
  hasAlert: boolean;
}

export default function SkuChart({ sku, colorIdx, hasAlert }: SkuChartProps) {
  const color = COLORS[colorIdx % COLORS.length];

  const chartData: (ForecastDay & { upperBound: number | null; lowerBound: number | null })[] =
    sku.forecast.slice(0, 30).map((d) => ({
      ...d,
      date: (() => {
        const dt = new Date(d.date);
        return dt.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
      })(),
      upperBound: d.upper_bound ?? null,
      lowerBound: d.lower_bound ?? null,
    }));

  return (
    <div className="bg-canvas border border-hairline rounded-lg p-5 relative">
      {hasAlert && (
        <div className="absolute top-3 right-3">
          <AlertTriangle className="w-4 h-4 text-red-600" />
        </div>
      )}

      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-card-title text-ink">{sku.product_name}</h3>
          <p className="text-mono text-ink-muted mt-0.5">SKU: {sku.sku_code}</p>
        </div>
        <div className="text-right">
          <p className="text-[24px] font-medium text-ink tabular-nums leading-none">{sku.predicted_demand_30d.toFixed(0)}</p>
          <p className="text-caption text-ink-muted mt-0.5">30d forecast</p>
        </div>
      </div>

      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }} aria-label="Demand forecast chart">
            <defs>
              <linearGradient id={`grad-${sku.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.15} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
              <linearGradient id={`confidence-${sku.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.08} />
                <stop offset="100%" stopColor={color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-hairline)" horizontal={true} vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: 'var(--color-ink-faint)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--color-hairline)', strokeWidth: 0.5 }}
            />
            <YAxis tick={{ fontSize: 11, fill: 'var(--color-ink-faint)' }} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-canvas)',
                border: '1px solid var(--color-hairline)',
                borderRadius: '6px',
                fontSize: '12px',
              }}
              labelStyle={{ fontSize: '11px', color: 'var(--color-ink-faint)' }}
            />
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke={color}
              strokeWidth={1}
              strokeDasharray="4 4"
              fill="none"
              dot={false}
              activeDot={false}
            />
            <Area
              type="monotone"
              dataKey="lowerBound"
              stroke={color}
              strokeWidth={1}
              strokeDasharray="4 4"
              fill="none"
              dot={false}
              activeDot={false}
            />
            <Area
              type="monotone"
              dataKey="lowerBound"
              stroke="none"
              fill={`url(#confidence-${sku.id})`}
              dot={false}
              activeDot={false}
            />
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="none"
              fill={`url(#confidence-${sku.id})`}
              dot={false}
              activeDot={false}
            />
            <Area
              type="monotone"
              dataKey="demand"
              stroke={color}
              strokeWidth={2}
              fill={`url(#grad-${sku.id})`}
              dot={false}
              activeDot={{ r: 4, fill: color }}
            />
            <ReferenceLine
              y={sku.reorder_point}
              stroke="#854F0B"
              strokeWidth={1}
              strokeDasharray="4 4"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-hairline">
        <div className="flex items-center gap-1.5 text-caption text-ink-muted">
          <TrendingUp className="w-3.5 h-3.5" />
          Stock: <span className="tabular-nums">{sku.current_stock}</span>
          {sku.stockout_risk && (
            <span className="ml-2 text-red-600 font-medium">At risk</span>
          )}
        </div>
        <span className="text-caption px-1.5 py-0.5 rounded-sm bg-purple-50 text-purple-800 border border-purple-100 dark:bg-purple-900/30 dark:text-purple-200 dark:border-purple-800">
          {sku.confidence_score}% confidence
        </span>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-caption text-ink-secondary" aria-label={`Forecast data for ${sku.product_name}`}>
          <thead>
            <tr className="border-b border-hairline">
              <th className="text-left py-1 pr-2 font-medium text-ink-faint">Date</th>
              <th className="text-right py-1 px-2 font-medium text-ink-faint">Demand</th>
              <th className="text-right py-1 px-2 font-medium text-ink-faint">Lower</th>
              <th className="text-right py-1 pl-2 font-medium text-ink-faint">Upper</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((d) => (
              <tr key={d.date} className="border-b border-hairline hover:bg-canvas-soft">
                <td className="py-1 pr-2 tabular-nums">{d.date}</td>
                <td className="text-right py-1 px-2 tabular-nums">{d.demand.toFixed(1)}</td>
                <td className="text-right py-1 px-2 tabular-nums text-ink-faint">
                  {d.lowerBound !== null ? d.lowerBound.toFixed(1) : '—'}
                </td>
                <td className="text-right py-1 pl-2 tabular-nums text-ink-faint">
                  {d.upperBound !== null ? d.upperBound.toFixed(1) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
