import type { ReactNode } from 'react';
import { Sparkles } from 'lucide-react';

const statusStyles: Record<string, string> = {
  'In Stock': 'bg-green-50 text-green-800 before:bg-green-600',
  'Low Stock': 'bg-amber-50 text-amber-800 before:bg-amber-600',
  'Out of Stock': 'bg-red-50 text-red-800 before:bg-red-600',
  Draft: 'bg-gray-100 text-gray-600',
  'Pending Approval': 'bg-amber-50 text-amber-800',
  Approved: 'bg-green-50 text-green-800',
  Sent: 'bg-brand-50 text-brand-800',
  Confirmed: 'bg-green-50 text-green-800',
  Rejected: 'bg-red-50 text-red-800',
  'AI Generated': 'bg-purple-50 text-purple-800',
  Viewer: 'bg-gray-100 text-gray-600',
  Manager: 'bg-brand-50 text-brand-800',
  Admin: 'bg-purple-50 text-purple-800',
};

interface BadgeProps {
  children?: ReactNode;
  variant?: keyof typeof statusStyles;
  showDot?: boolean;
}

export default function Badge({ children, variant, showDot = true }: BadgeProps) {
  const styleKey = variant || (children ? String(children) : 'Draft');
  const classes = statusStyles[styleKey];
  const isAi = styleKey === 'AI Generated';

  if (!classes) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-caption font-medium bg-gray-100 text-gray-600">
        {children}
      </span>
    );
  }

  const hasDot = showDot && classes.includes('before:');

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-caption font-medium ${classes} ${
        hasDot ? 'before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:shrink-0' : ''
      }`}
    >
      {isAi && <Sparkles className="w-3 h-3" />}
      {children}
    </span>
  );
}
