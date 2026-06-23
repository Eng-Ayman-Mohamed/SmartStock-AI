import { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { LogOut, Menu, User as UserIcon } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useUIStore } from '../../store/uiStore';
import { useAuth } from '../../features/auth/hooks/useAuth';
import { useServerHealth } from '../../shared/hooks/useServerHealth';
import RoleBadge from '../../features/users/components/RoleBadge';
import { getAvatarColor } from '../../shared/utils/avatar';
import ThemeToggle from './ThemeToggle';
import NotificationBell from '../../features/notifications/components/NotificationBell';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/inventory': 'Inventory',
  '/forecasting': 'Forecasting',
  '/purchasing': 'Purchasing',
  '/ai-assistant': 'AI Assistant',
  '/documents': 'Documents',
  '/invoice-scan': 'Invoice Scan',
  '/settings': 'Team & permissions',
  '/profile': 'Profile',
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
  const { data: isAlive, isLoading: healthLoading } = useServerHealth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const title = pageTitles[location.pathname] || 'SmartStock AI';

  useEffect(() => {
    if (!menuOpen) return;
    const menu = menuRef.current;
    if (!menu) return;
    const focusable = menu.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    first?.focus();
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Tab') return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [menuOpen]);

  async function onSignOut() {
    setMenuOpen(false);
    await logout();
    navigate('/login', { replace: true });
  }

  function onProfile() {
    setMenuOpen(false);
    navigate('/profile');
  }

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-10 px-4 sm:px-6 border-b border-hairline bg-canvas">
      <div className="flex items-center gap-2 min-w-0 shrink">
        <button
          onClick={toggleSidebar}
          className="md:hidden flex items-center justify-center w-7 h-7 rounded-md text-ink-faint hover:text-ink-secondary hover:bg-canvas-soft transition-colors shrink-0"
          aria-label="Toggle navigation"
        >
          <Menu className="w-4 h-4" />
        </button>
        <nav aria-label="Breadcrumb" className="min-w-0">
          <ol className="flex items-center gap-1.5 text-caption text-ink-muted">
            <li className="hidden sm:inline">SmartStock AI</li>
            <li aria-hidden="true" className="text-ink-faint hidden sm:inline">/</li>
            <li className="text-ink font-medium truncate" aria-current="page">{title}</li>
          </ol>
        </nav>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <div className="flex items-center gap-1.5" title={healthLoading ? 'Checking...' : isAlive ? 'Server online' : 'Server offline'}>
          <span className={`w-2 h-2 rounded-full ${
            healthLoading ? 'bg-gray-300' : isAlive ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="text-caption text-ink-muted hidden sm:inline">
            {healthLoading ? '...' : isAlive ? 'Online' : 'Offline'}
          </span>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-3">
          <ThemeToggle />
          <NotificationBell />

          {user && (
            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((o) => !o)}
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                className="flex items-center gap-2 rounded-md px-1 py-0.5 hover:bg-canvas-soft transition-colors"
              >
                <div
                  className={`w-7 h-7 rounded-full ${getAvatarColor(user.name)} flex items-center justify-center text-white text-[11px] font-medium`}
                  aria-hidden="true"
                >
                  {getInitials(user.name)}
                </div>
                <span className="hidden sm:inline text-caption font-medium text-ink-muted">{user.name}</span>
                {user.role && <RoleBadge role={user.role} className="hidden sm:inline-flex" />}
              </button>

              {menuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setMenuOpen(false)}
                    aria-hidden="true"
                  />
                  <div
                    ref={menuRef}
                    role="menu"
                    className="absolute right-0 mt-1 w-48 rounded-lg border border-hairline bg-canvas shadow-soft z-50 py-1"
                  >
                    <div className="px-3 py-2 border-b border-hairline">
                      <p className="text-caption font-medium text-ink truncate">{user.name}</p>
                      <p className="text-caption text-ink-muted truncate">{user.email}</p>
                      {user.role && <RoleBadge role={user.role} className="mt-1" />}
                    </div>
                    <button
                      type="button"
                      role="menuitem"
                      onClick={onProfile}
                      className="w-full flex items-center gap-2 px-3 py-2 text-caption text-ink hover:bg-canvas-soft"
                    >
                      <UserIcon className="w-4 h-4" aria-hidden="true" />
                      <span>Profile</span>
                    </button>
                    <button
                      type="button"
                      role="menuitem"
                      onClick={onSignOut}
                      disabled={isSubmitting}
                      className="w-full flex items-center gap-2 px-3 py-2 text-caption text-ink hover:bg-canvas-soft disabled:opacity-50 disabled:cursor-not-allowed"
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
      </div>
    </header>
  );
}
