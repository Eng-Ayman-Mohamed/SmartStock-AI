import { Navigate, Outlet, useLocation, type Location } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuthStore, type Role } from '../../../store/authStore';

interface ProtectedRouteProps {
  allowedRoles?: Role[];
}

export default function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((s) => Boolean(s.token && s.user));
  const user = useAuthStore((s) => s.user);
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
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-6 h-6 text-brand-600 animate-spin" aria-hidden="true" />
          <span className="text-caption text-gray-600">Restoring your session…</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    if (!user || !allowedRoles.includes(user.role)) {
      return <Navigate to="/forbidden" replace />;
    }
  }

  return <Outlet />;
}

export type { Location };
