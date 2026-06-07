import { Eye, UserCog, ShieldCheck } from 'lucide-react';
import type { Role } from '../types';

interface RoleBadgeProps {
  role: Role;
  className?: string;
}

const ROLE_META: Record<Role, { label: string; icon: typeof Eye; className: string }> = {
  viewer: {
    label: 'Viewer',
    icon: Eye,
    className: 'bg-gray-100 text-gray-700',
  },
  manager: {
    label: 'Manager',
    icon: UserCog,
    className: 'bg-brand-50 text-brand-800',
  },
  admin: {
    label: 'Admin',
    icon: ShieldCheck,
    className: 'bg-purple-50 text-purple-800',
  },
};

export default function RoleBadge({ role, className = '' }: RoleBadgeProps) {
  const meta = ROLE_META[role];
  const Icon = meta.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm text-caption font-medium ${meta.className} ${className}`}
    >
      <Icon className="w-3 h-3" aria-hidden="true" />
      <span className="capitalize">{meta.label}</span>
    </span>
  );
}

export { ROLE_META };
