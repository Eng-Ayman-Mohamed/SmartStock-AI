import { useState, useMemo } from 'react';
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
  allSkus?: SkuForecast[];
  colorIdx: number;
  hasAlert: boolean;
}

export default function SkuChart({ sku, allSkus, colorIdx, hasAlert }: SkuChartProps) {
  const [selectedSkuId, setSelectedSkuId] = useState(sku.id);
  const skus = allSkus ?? [sku];
  const activeSku = useMemo(
    () => skus.find((s) => s.id === selectedSkuId) ?? sku,
    [skus, selectedSkuId, sku],
  );
  const color = COLORS[colorIdx % COLORS.length];

  const chartData: (ForecastDay & { upperBound: number | null; lowerBound: number | null })[] =
    activeSku.forecast.slice(0, 30).map((d) => ({
      ...d,
      date: (() => {
        const dt = new Date(d.date);
        return dt.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
      })(),
      upperBound: d.upper_bound ?? null,
      lowerBound: d.lower_bound ?? null,
    }));

  return (
    <div className="bg-white border-[0.5px] border-gray-100 rounded-lg p-5 relative">
      {hasAlert && (
        <div className="absolute top-3 right-3">
          <AlertTriangle className="w-4 h-4 text-red-600" />
        </div>
      )}

      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-card-title text-gray-900">{activeSku.product_name}</h3>
          <p className="text-mono text-gray-600 mt-0.5">SKU: {activeSku.sku_code}</p>
        </div>
        <div className="text-right">
          <p className="text-[24px] font-medium text-gray-900 tabular-nums leading-none">{activeSku.predicted_demand_30d.toFixed(0)}</p>
          <p className="text-caption text-gray-600 mt-0.5">30d forecast</p>
        </div>
      </div>

      {skus.length > 1 && (
        <div className="mb-4">
          <select
            value={selectedSkuId}
            onChange={(e) => setSelectedSkuId(e.target.value)}
            className="w-full h-9 px-3 rounded-md border border-gray-200 bg-white text-body text-gray-800 hover:border-gray-400 focus:border-brand-600 focus:outline-none transition-colors"
            aria-label="Select SKU"
          >
            {skus.map((s) => (
              <option key={s.id} value={s.id}>
                {s.product_name} ({s.sku_code})
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
            <defs>
              <linearGradient id={`grad-${activeSku.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.15} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
              <linearGradient id={`confidence-${activeSku.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.08} />
                <stop offset="100%" stopColor={color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#D3D1C7" horizontal={true} vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: '#888780' }}
              tickLine={false}
              axisLine={{ stroke: '#D3D1C7', strokeWidth: 0.5 }}
            />
            <YAxis tick={{ fontSize: 11, fill: '#888780' }} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: 'none',
                borderRadius: '6px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
                fontSize: '12px',
              }}
              labelStyle={{ fontSize: '11px', color: '#888780' }}
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
              fill={`url(#confidence-${activeSku.id})`}
              dot={false}
              activeDot={false}
            />
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="none"
              fill={`url(#confidence-${activeSku.id})`}
              dot={false}
              activeDot={false}
            />
            <Area
              type="monotone"
              dataKey="demand"
              stroke={color}
              strokeWidth={2}
              fill={`url(#grad-${activeSku.id})`}
              dot={false}
              activeDot={{ r: 4, fill: color }}
            />
            <ReferenceLine
              y={activeSku.reorder_point}
              stroke="#854F0B"
              strokeWidth={1}
              strokeDasharray="4 4"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between mt-3 pt-3 border-t-[0.5px] border-gray-100">
        <div className="flex items-center gap-1.5 text-caption text-gray-600">
          <TrendingUp className="w-3.5 h-3.5" />
          Stock: <span className="tabular-nums">{activeSku.current_stock}</span>
          {activeSku.stockout_risk && (
            <span className="ml-2 text-red-600 font-medium">At risk</span>
          )}
        </div>
        <span className="text-caption px-1.5 py-0.5 rounded-sm bg-purple-50 text-purple-800 border-[0.5px] border-purple-100">
          {activeSku.confidence_score}% confidence
        </span>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-caption text-gray-700" aria-label={`Forecast data for ${activeSku.product_name}`}>
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-1 pr-2 font-medium text-gray-500">Date</th>
              <th className="text-right py-1 px-2 font-medium text-gray-500">Demand</th>
              <th className="text-right py-1 px-2 font-medium text-gray-500">Lower</th>
              <th className="text-right py-1 pl-2 font-medium text-gray-500">Upper</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((d) => (
              <tr key={d.date} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="py-1 pr-2 tabular-nums">{d.date}</td>
                <td className="text-right py-1 px-2 tabular-nums">{d.demand.toFixed(1)}</td>
                <td className="text-right py-1 px-2 tabular-nums text-gray-400">
                  {d.lowerBound !== null ? d.lowerBound.toFixed(1) : '—'}
                </td>
                <td className="text-right py-1 pl-2 tabular-nums text-gray-400">
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
