import { Eye, UserCog, ShieldCheck, FlaskConical } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import type { Role } from '../types';

interface RoleOption {
  role: Role;
  label: string;
  description: string;
  icon: typeof Eye;
  accent: string;
}

const OPTIONS: RoleOption[] = [
  {
    role: 'viewer',
    label: 'Viewer',
    description: 'Read-only access to inventory and forecasts',
    icon: Eye,
    accent: 'text-gray-600 bg-gray-50 hover:bg-gray-100 border-gray-200',
  },
  {
    role: 'manager',
    label: 'Manager',
    description: 'Approve POs, edit inventory, manage suppliers',
    icon: UserCog,
    accent: 'text-brand-700 bg-brand-50 hover:bg-brand-100 border-brand-200',
  },
  {
    role: 'admin',
    label: 'Admin',
    description: 'Full access including user management and Settings',
    icon: ShieldCheck,
    accent: 'text-purple-700 bg-purple-50 hover:bg-purple-100 border-purple-200',
  },
];

export default function DemoLoginPanel() {
  const { loginAsRole, isSubmitting } = useAuth();

  return (
    <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 mb-3">
        <FlaskConical className="w-4 h-4 text-amber-700" aria-hidden="true" />
        <p className="text-caption font-semibold text-amber-800 uppercase tracking-wide">
          Dev mode · backend not connected
        </p>
      </div>
      <p className="text-caption text-amber-900 mb-3">
        Sign in as a demo user to explore the app. No real authentication is performed.
      </p>
      <div className="grid grid-cols-1 gap-2">
        {OPTIONS.map((opt) => {
          const Icon = opt.icon;
          return (
            <button
              key={opt.role}
              type="button"
              disabled={isSubmitting}
              onClick={() => loginAsRole(opt.role, '/')}
              className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-md border text-left transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${opt.accent}`}
            >
              <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
              <div className="min-w-0">
                <p className="text-caption font-semibold">Continue as {opt.label}</p>
                <p className="text-caption opacity-80">{opt.description}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
