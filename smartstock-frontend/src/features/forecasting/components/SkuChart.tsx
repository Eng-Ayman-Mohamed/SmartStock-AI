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
import type { SkuForecast } from '../hooks/useForecastDashboard';

const COLORS = ['#185FA5', '#3B6D11', '#854F0B', '#A32D2D', '#378ADD', '#534AB7', '#D14545', '#2675C9'];

interface SkuChartProps {
  sku: SkuForecast;
  colorIdx: number;
  hasAlert: boolean;
}

export default function SkuChart({ sku, colorIdx, hasAlert }: SkuChartProps) {
  const color = COLORS[colorIdx % COLORS.length];
  const chartData = sku.forecast.slice(0, 30).map((d) => ({
    date: d.date.slice(0, 5),
    demand: d.predicted_demand,
  }));

  return (
    <div className="bg-white border-[0.5px] border-gray-100 rounded-lg p-5">
      {hasAlert && (
        <div className="absolute top-3 right-3">
          <AlertTriangle className="w-4 h-4 text-red-600" />
        </div>
      )}

      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-card-title text-gray-900">{sku.product_name}</h3>
          <p className="text-mono text-gray-600 mt-0.5">SKU: {sku.sku_code}</p>
        </div>
        <div className="text-right">
          <p className="text-[24px] font-medium text-gray-900 tabular-nums leading-none">{sku.predicted_demand_30d.toFixed(0)}</p>
          <p className="text-caption text-gray-600 mt-0.5">30d forecast</p>
        </div>
      </div>

      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#D3D1C7" horizontal={true} vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#888780' }} tickLine={false} axisLine={{ stroke: '#D3D1C7', strokeWidth: 0.5 }} />
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
            <defs>
              <linearGradient id={`grad-${sku.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.15} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
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

      <div className="flex items-center justify-between mt-3 pt-3 border-t-[0.5px] border-gray-100">
        <div className="flex items-center gap-1.5 text-caption text-gray-600">
          <TrendingUp className="w-3.5 h-3.5" />
          Stock: <span className="tabular-nums">{sku.current_stock}</span>
        </div>
        <span className="text-caption px-1.5 py-0.5 rounded-sm bg-purple-50 text-purple-800 border-[0.5px] border-purple-100">
          {sku.confidence_score}% confidence
        </span>
      </div>
    </div>
  );
}
