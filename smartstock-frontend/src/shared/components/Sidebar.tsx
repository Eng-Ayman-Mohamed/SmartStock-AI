import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  TrendingUp,
  ShoppingCart,
  Bot,
  Scan,
  Settings,
  User as UserIcon,
  ChevronLeft,
  ChevronRight,
  X,
  Sparkles,
  Users,
} from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { useAuthStore } from '../../store/authStore';

const mainNavItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inventory', icon: Package, label: 'Inventory' },
  { to: '/forecasting', icon: TrendingUp, label: 'Forecasting' },
  { to: '/purchasing', icon: ShoppingCart, label: 'Purchasing' },
  { to: '/suppliers', icon: Users, label: 'Suppliers' },
  { to: '/ai-assistant', icon: Bot, label: 'AI Assistant', accent: true },
  { to: '/invoice-scan', icon: Scan, label: 'Invoice Scan' },
];

function BottomNavItem({ collapsed, onClick }: { collapsed: boolean; onClick?: () => void }) {
  const role = useAuthStore((s) => s.user?.role);
  const isAdmin = role === 'admin';
  const to = isAdmin ? '/settings' : '/profile';
  const Icon = isAdmin ? Settings : UserIcon;
  const label = isAdmin ? 'Team & permissions' : 'Profile';

  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center h-10 rounded-md text-body transition-colors duration-150 group relative ${
          collapsed ? 'justify-center px-0 w-10 mx-auto' : 'gap-3 px-3'
        } ${
          isActive
            ? 'bg-brand-50 text-brand-800 border-l-2 border-brand-600'
            : 'text-ink-secondary hover:bg-canvas-soft hover:text-ink'
        }`
      }
    >
      <Icon className="w-[18px] h-[18px] shrink-0" aria-hidden="true" />
      {!collapsed && <span className="truncate">{label}</span>}
      {collapsed && (
        <span className="absolute left-full ml-2 px-2 py-1 rounded-md bg-gray-900 text-white text-caption whitespace-nowrap z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 pointer-events-none">
          {label}
        </span>
      )}
    </NavLink>
  );
}

export default function Sidebar() {
  const { sidebarOpen, setSidebarOpen, sidebarCollapsed, setSidebarCollapsed } = useUIStore();

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)');
    const handler = (e: MediaQueryListEvent | MediaQueryList) => {
      if (e.matches) {
        setSidebarCollapsed(true);
      }
    };
    handler(mq);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [setSidebarCollapsed]);

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={`fixed top-0 left-0 h-screen z-50 flex flex-col bg-canvas border-r border-hairline transition-all duration-200 md:hidden w-[220px] ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Navigation sidebar"
      >
        <div className="flex items-center justify-between h-10 px-3 border-b border-hairline">
          <span className="text-card-title font-medium text-ink">SmartStock AI</span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="flex items-center justify-center w-7 h-7 rounded-md text-ink-faint hover:text-ink-secondary hover:bg-canvas-soft transition-colors"
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <nav className="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto">
          {mainNavItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 h-10 px-3 rounded-md text-body transition-colors duration-150 ${
                  isActive
                    ? 'bg-brand-50 text-brand-800 border-l-2 border-brand-600'
                    : 'text-ink-secondary hover:bg-canvas-soft hover:text-ink'
                }`
              }
            >
              <item.icon
                className={`w-[18px] h-[18px] shrink-0 ${item.accent ? 'text-purple-600' : ''}`}
                aria-hidden="true"
              />
              <span className="truncate">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="px-2 py-2 border-t border-hairline">
          <BottomNavItem collapsed={false} onClick={() => setSidebarOpen(false)} />
        </div>
      </aside>

      {/* Desktop sidebar */}
      <aside
        className={`hidden md:flex flex-col bg-canvas border-r border-hairline shrink-0 min-h-screen sticky top-0 h-screen transition-all duration-200 ${
          sidebarCollapsed ? 'w-14' : 'w-[220px]'
        }`}
        aria-label="Navigation sidebar"
      >
        <div className={`flex items-center h-10 px-3 border-b border-hairline ${sidebarCollapsed ? 'justify-center' : 'gap-2'}`}>
          <Sparkles className="w-4 h-4 text-brand-600 shrink-0" aria-hidden="true" />
          {!sidebarCollapsed && <span className="text-card-title font-medium text-ink truncate">SmartStock AI</span>}
        </div>

        <nav className="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto">
          <div className="space-y-0.5">
            {mainNavItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center h-10 rounded-md text-body transition-colors duration-150 group relative ${
                    sidebarCollapsed ? 'justify-center px-0 w-10 mx-auto' : 'gap-3 px-3'
                  } ${
                    isActive
                      ? 'bg-brand-50 text-brand-800 border-l-2 border-brand-600'
                      : 'text-ink-secondary hover:bg-canvas-soft hover:text-ink'
                  }`
                }
              >
                <item.icon
                  className={`w-[18px] h-[18px] shrink-0 ${item.accent ? 'text-purple-600' : ''}`}
                  aria-hidden="true"
                />
                {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
                {sidebarCollapsed && (
                  <span className="absolute left-full ml-2 px-2 py-1 rounded-md bg-gray-900 text-white text-caption whitespace-nowrap z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 pointer-events-none">
                    {item.label}
                  </span>
                )}
              </NavLink>
            ))}
          </div>

          <div className="pt-2 mt-2 border-t border-hairline">
            <BottomNavItem collapsed={sidebarCollapsed} />
          </div>
        </nav>

        <div className="px-2 py-2 border-t border-hairline">
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="flex items-center justify-center w-full h-9 rounded-md text-ink-faint hover:text-ink-secondary hover:bg-canvas-soft transition-colors duration-150"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </aside>
    </>
  );
}
