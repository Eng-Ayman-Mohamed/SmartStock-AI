import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Package, Bot, ShoppingCart, User as UserIcon } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
  { to: '/inventory', icon: Package, label: 'Inventory' },
  { to: '/ai-assistant', icon: Bot, label: 'AI', accent: true },
  { to: '/purchasing', icon: ShoppingCart, label: 'Orders' },
  { to: '/profile', icon: UserIcon, label: 'Profile' },
];

export default function BottomNav() {
  const role = useAuthStore((s) => s.user?.role);
  const items = navItems.map((item) => {
    if (item.to === '/profile' && role === 'admin') {
      return { ...item, to: '/settings', label: 'Team' };
    }
    return item;
  });

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 md:hidden bg-canvas border-t border-hairline safe-area-pb"
      aria-label="Mobile navigation"
    >
      <div className="flex items-center justify-around h-14">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center gap-0.5 w-full h-full text-eyebrow transition-colors ${
                isActive
                  ? 'text-brand-600 dark:text-brand-400'
                  : 'text-ink-faint hover:text-ink-muted'
              }`
            }
          >
            <item.icon className={`w-5 h-5 ${item.accent ? 'text-purple-600 dark:text-purple-400' : ''}`} aria-hidden="true" />
            <span className={`text-[11px] leading-tight ${item.accent ? 'text-purple-600 dark:text-purple-400' : ''}`}>{item.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
