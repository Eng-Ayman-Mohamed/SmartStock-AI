import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell, LogOut, Menu } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useUIStore } from '../../store/uiStore';
import { useAuth } from '../../features/auth/hooks/useAuth';

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/inventory': 'Inventory',
  '/forecasting': 'Forecasting',
  '/purchasing': 'Purchasing',
  '/ai-assistant': 'AI Assistant',
  '/invoice-scan': 'Invoice Scan',
  '/settings': 'Settings',
};

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const { logout, isSubmitting } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const title = pageTitles[location.pathname] || 'SmartStock AI';

  async function onSignOut() {
    setMenuOpen(false);
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-10 px-4 sm:px-6 border-b-[1px] border-gray-100 bg-white">
      <div className="flex items-center gap-2">
        <button
          onClick={toggleSidebar}
          className="md:hidden flex items-center justify-center w-7 h-7 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
          aria-label="Toggle navigation"
        >
          <Menu className="w-4 h-4" />
        </button>
        <nav aria-label="Breadcrumb">
          <ol className="flex items-center gap-1.5 text-caption text-gray-600">
            <li>SmartStock AI</li>
            <li aria-hidden="true" className="text-gray-300">/</li>
            <li className="text-gray-900 font-medium" aria-current="page">{title}</li>
          </ol>
        </nav>
      </div>

      <div className="flex items-center gap-3">
        <button
          className="relative flex items-center justify-center w-7 h-7 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
        </button>

        {user && (
          <div className="relative">
            <button
              type="button"
              onClick={() => setMenuOpen((o) => !o)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              className="flex items-center gap-2 rounded-md px-1 py-0.5 hover:bg-gray-50 transition-colors"
            >
              <div
                className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-white text-[11px] font-medium"
                aria-hidden="true"
              >
                {getInitials(user.name)}
              </div>
              <span className="hidden sm:inline text-caption font-medium text-gray-600">{user.name}</span>
              <span className="hidden lg:inline-flex items-center px-1.5 py-0.5 rounded-sm text-caption font-medium bg-brand-50 text-brand-800 capitalize">
                {user.role}
              </span>
            </button>

            {menuOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setMenuOpen(false)}
                  aria-hidden="true"
                />
                <div
                  role="menu"
                  className="absolute right-0 mt-1 w-48 rounded-md border border-gray-100 bg-white shadow-lg z-50 py-1"
                >
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="text-caption font-medium text-gray-900 truncate">{user.name}</p>
                    <p className="text-caption text-gray-600 truncate">{user.email}</p>
                  </div>
                  <button
                    type="button"
                    role="menuitem"
                    onClick={onSignOut}
                    disabled={isSubmitting}
                    className="w-full flex items-center gap-2 px-3 py-2 text-caption text-gray-900 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <LogOut className="w-4 h-4" aria-hidden="true" />
                    <span>Sign out</span>
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
