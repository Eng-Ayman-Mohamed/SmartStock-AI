import { useLocation } from 'react-router-dom';
import { Search, Bell, User } from 'lucide-react';

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/inventory': 'Inventory',
  '/forecasting': 'Forecasting',
  '/purchasing': 'Purchasing',
};

export default function Header() {
  const location = useLocation();
  const title = pageTitles[location.pathname] || 'SmartStock AI';

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 border-b border-surface-800/50 bg-surface-950/60 backdrop-blur-lg">
      <h1 className="text-xl font-semibold text-surface-100">{title}</h1>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
          <input
            type="text"
            placeholder="Search..."
            className="w-64 h-9 pl-10 pr-4 rounded-lg bg-surface-800/60 border border-surface-700/50 text-sm text-surface-200 placeholder:text-surface-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500/50 transition-all duration-200"
          />
        </div>

        {/* Notifications */}
        <button className="relative flex items-center justify-center w-9 h-9 rounded-lg text-surface-400 hover:text-surface-200 hover:bg-surface-800/60 transition-colors duration-200">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-brand-500 rounded-full animate-pulse" />
        </button>

        {/* User Avatar */}
        <button className="flex items-center justify-center w-9 h-9 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-lg shadow-brand-500/20 hover:shadow-brand-500/40 transition-shadow duration-200">
          <User className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
