import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  TrendingUp,
  ShoppingCart,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inventory', icon: Package, label: 'Inventory' },
  { to: '/forecasting', icon: TrendingUp, label: 'Forecasting' },
  { to: '/purchasing', icon: ShoppingCart, label: 'Purchasing' },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`fixed top-0 left-0 h-screen z-40 flex flex-col border-r border-surface-800/50 bg-surface-900/80 backdrop-blur-xl transition-all duration-300 ease-in-out ${
        collapsed ? 'w-[72px]' : 'w-64'
      }`}
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 h-16 border-b border-surface-800/50">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 shadow-lg shadow-brand-500/25">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <span className="text-lg font-bold bg-gradient-to-r from-brand-300 to-brand-500 bg-clip-text text-transparent whitespace-nowrap">
            SmartStock AI
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-brand-500/15 text-brand-400 shadow-sm shadow-brand-500/10'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/60'
              }`
            }
          >
            <item.icon className="w-5 h-5 shrink-0" />
            {!collapsed && <span className="whitespace-nowrap">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-surface-800/50">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full h-9 rounded-lg text-surface-400 hover:text-surface-200 hover:bg-surface-800/60 transition-colors duration-200"
        >
          {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>
    </aside>
  );
}
