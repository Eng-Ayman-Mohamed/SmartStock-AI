import { Package, TrendingUp, ShoppingCart, AlertTriangle } from 'lucide-react';

const stats = [
  { label: 'Total Products', value: '—', icon: Package, color: 'from-brand-500 to-brand-700', shadow: 'shadow-brand-500/20' },
  { label: 'Active Forecasts', value: '—', icon: TrendingUp, color: 'from-emerald-500 to-emerald-700', shadow: 'shadow-emerald-500/20' },
  { label: 'Pending Orders', value: '—', icon: ShoppingCart, color: 'from-amber-500 to-amber-700', shadow: 'shadow-amber-500/20' },
  { label: 'Low Stock Alerts', value: '—', icon: AlertTriangle, color: 'from-red-500 to-red-700', shadow: 'shadow-red-500/20' },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="relative overflow-hidden rounded-2xl border border-surface-800/50 bg-surface-900/60 backdrop-blur-sm p-5 hover:border-surface-700/60 transition-all duration-300 group"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-surface-400 font-medium">{stat.label}</p>
                <p className="mt-1 text-2xl font-bold text-surface-100">{stat.value}</p>
              </div>
              <div className={`flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br ${stat.color} shadow-lg ${stat.shadow} group-hover:scale-110 transition-transform duration-300`}>
                <stat.icon className="w-5 h-5 text-white" />
              </div>
            </div>
            {/* Decorative gradient */}
            <div className={`absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-gradient-to-br ${stat.color} opacity-5 blur-2xl group-hover:opacity-10 transition-opacity duration-500`} />
          </div>
        ))}
      </div>

      {/* Placeholder sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-surface-800/50 bg-surface-900/60 backdrop-blur-sm p-6 min-h-[320px]">
          <h2 className="text-lg font-semibold text-surface-200 mb-4">Demand Forecast</h2>
          <div className="flex items-center justify-center h-56 rounded-xl border-2 border-dashed border-surface-800 text-surface-600">
            <p className="text-sm">Chart will be rendered here</p>
          </div>
        </div>
        <div className="rounded-2xl border border-surface-800/50 bg-surface-900/60 backdrop-blur-sm p-6 min-h-[320px]">
          <h2 className="text-lg font-semibold text-surface-200 mb-4">Recent Activity</h2>
          <div className="flex items-center justify-center h-56 rounded-xl border-2 border-dashed border-surface-800 text-surface-600">
            <p className="text-sm">Activity feed will appear here</p>
          </div>
        </div>
      </div>
    </div>
  );
}
