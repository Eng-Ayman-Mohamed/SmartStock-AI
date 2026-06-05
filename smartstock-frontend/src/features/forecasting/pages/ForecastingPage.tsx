import { TrendingUp, RefreshCw } from 'lucide-react';

export default function ForecastingPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-surface-100">Demand Forecasting</h2>
          <p className="text-sm text-surface-400 mt-1">AI-powered 30-day demand predictions per SKU</p>
        </div>
        <button className="flex items-center gap-2 h-9 px-4 rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-500 text-sm font-medium text-white shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 transition-all duration-200">
          <RefreshCw className="w-4 h-4" />
          Run Forecast
        </button>
      </div>

      <div className="rounded-2xl border border-surface-800/50 bg-surface-900/60 backdrop-blur-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-surface-800/50">
          <div className="flex items-center gap-2 text-surface-400">
            <TrendingUp className="w-4 h-4" />
            <span className="text-sm font-medium">Forecast Results</span>
          </div>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-center h-64 rounded-xl border-2 border-dashed border-surface-800 text-surface-600">
            <p className="text-sm">Forecast chart and data will appear here</p>
          </div>
        </div>
      </div>
    </div>
  );
}
