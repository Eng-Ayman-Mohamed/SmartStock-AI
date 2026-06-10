import { type LucideIcon } from 'lucide-react';

type Accent = 'orange' | 'purple' | 'green' | 'red' | 'none';

const accentBorders: Record<Accent, string> = {
  orange: 'border-l-2 border-l-orange-600',
  purple: 'border-l-2 border-l-purple-600',
  green: 'border-l-2 border-l-green-600',
  red: 'border-l-2 border-l-red-600',
  none: '',
};

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: {
    direction: 'up' | 'down';
    percentage: string;
    color?: string;
  };
  icon?: LucideIcon;
  accent?: Accent;
}

export default function StatCard({ label, value, trend, icon: Icon, accent = 'none' }: StatCardProps) {
  return (
    <div className={`bg-canvas rounded-lg border border-hairline p-6 h-24 min-w-[160px] flex flex-col justify-between ${accentBorders[accent]}`}>
      <div className="flex items-center justify-between">
        <span className="text-caption font-medium text-ink-muted uppercase tracking-[0.05em]">{label}</span>
        {Icon && <Icon className="w-4 h-4 text-ink-faint" aria-hidden="true" />}
      </div>
      <div className="flex items-end justify-between">
        <span className="text-[26px] font-medium text-ink tabular-nums leading-none">{value}</span>
        {trend && (
          <span className={`text-caption tabular-nums ${
            trend.direction === 'up'
              ? (trend.color || 'text-green-600')
              : (trend.color || 'text-red-600')
          }`}>
            {trend.direction === 'up' ? '\u2191' : '\u2193'} {trend.percentage}
          </span>
        )}
      </div>
    </div>
  );
}
