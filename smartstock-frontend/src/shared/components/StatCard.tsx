import { type LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: {
    direction: 'up' | 'down';
    percentage: string;
    color?: string;
  };
  icon?: LucideIcon;
  accent?: 'amber' | 'purple' | 'green' | 'red' | 'none';
}

export default function StatCard({ label, value, trend, icon: Icon, accent = 'none' }: StatCardProps) {
  const accentBorder = accent !== 'none' ? 'border-l-2 border-l-' + (
    accent === 'amber' ? 'amber-600' :
    accent === 'purple' ? 'purple-600' :
    accent === 'green' ? 'green-600' :
    accent === 'red' ? 'red-600' : ''
  ) : '';

  return (
    <div className={`bg-white rounded-md border-[0.5px] border-gray-100 p-4 h-24 min-w-[160px] flex flex-col justify-between ${accentBorder}`}>
      <div className="flex items-center justify-between">
        <span className="text-caption font-medium text-gray-600 uppercase tracking-[0.05em]">{label}</span>
        {Icon && <Icon className="w-4 h-4 text-gray-400" aria-hidden="true" />}
      </div>
      <div className="flex items-end justify-between">
        <span className="text-[24px] font-medium text-gray-900 tabular-nums leading-none">{value}</span>
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
