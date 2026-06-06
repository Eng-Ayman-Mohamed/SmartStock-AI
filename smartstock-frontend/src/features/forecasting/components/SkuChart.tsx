import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer
} from 'recharts';
import type { ForecastSKU } from '../hooks/useForecastDashboard';

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#8b5cf6'];

interface Props { sku: ForecastSKU; colorIdx: number; hasAlert: boolean; }

export default function SkuChart({ sku, colorIdx, hasAlert }: Props) {
  const color = COLORS[colorIdx % COLORS.length];
  const belowDays = sku.days.filter(d => d.demand < sku.threshold).length;
  return (
    <div className={`rounded-2xl border bg-surface-900/60 p-5
      ${hasAlert ? 'border-danger/25' : 'border-surface-800/50'}`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-xs text-surface-500 font-mono mb-1">{sku.id}</p>
          <h3 className="text-base font-semibold text-surface-100">{sku.name}</h3>
        </div>
        <div className="text-right">
          <p className={`text-xl font-bold font-mono
            ${sku.current_stock < sku.threshold ? 'text-danger' : 'text-info'}`}>
            {sku.current_stock}
          </p>
          <p className="text-[10px] text-surface-600 font-mono">IN STOCK</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4">
        {[
          { label: 'threshold', value: sku.threshold },
          { label: 'days below', value: belowDays, warn: belowDays > 0 },
          { label: 'lead time', value: `${sku.lead_time_days}d` },
        ].map(s => (
          <div key={s.label} className="bg-surface-950 rounded-lg px-3 py-2">
            <p className="text-[9px] text-surface-600 font-mono uppercase tracking-wider mb-1">
              {s.label}
            </p>
            <p className={`text-sm font-bold font-mono ${s.warn ? 'text-danger' : 'text-surface-300'}`}>
              {s.value}
            </p>
          </div>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={140}>
        <AreaChart data={sku.days} margin={{ top: 4, right: 0, left: -22, bottom: 0 }}>
          <defs>
            <linearGradient id={`g-${sku.id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="date"
            tickFormatter={d => d.slice(5)}
            tick={{ fontSize: 9, fill: '#334155', fontFamily: 'monospace' }}
            tickLine={false} axisLine={false} interval={6} />
          <YAxis
            tick={{ fontSize: 9, fill: '#334155', fontFamily: 'monospace' }}
            tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: '#0f172a', border: '1px solid #1e293b',
              borderRadius: 6, fontSize: 11, fontFamily: 'monospace' }}
            labelStyle={{ color: '#64748b' }}
            itemStyle={{ color: color }} />
          <ReferenceLine y={sku.threshold} stroke="#ef4444"
            strokeDasharray="4 4" strokeOpacity={0.6} />
          <Area type="monotone" dataKey="demand"
            stroke={color} strokeWidth={2}
            fill={`url(#g-${sku.id})`} dot={false}
            activeDot={{ r: 3, strokeWidth: 0 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}