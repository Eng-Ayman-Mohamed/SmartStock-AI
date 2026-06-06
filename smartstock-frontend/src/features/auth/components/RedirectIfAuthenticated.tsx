import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '../../../store/authStore';

export default function RedirectIfAuthenticated() {
  const isAuthenticated = useAuthStore((s) => Boolean(s.token && s.user));
  const isBootstrapping = useAuthStore((s) => s.isBootstrapping);
  const location = useLocation();

  if (isBootstrapping) {
    return (
      <div
        className="min-h-screen flex items-center justify-center bg-gray-50"
        role="status"
        aria-live="polite"
        aria-label="Loading session"
      >
        <Loader2 className="w-6 h-6 text-brand-600 animate-spin" aria-hidden="true" />
      </div>
    );
  }

  if (isAuthenticated) {
    const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
    return <Navigate to={from && from !== '/login' && from !== '/register' ? from : '/'} replace />;
  }

  return <Outlet />;
}
