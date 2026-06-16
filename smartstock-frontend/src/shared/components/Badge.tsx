import type { ReactNode } from 'react';
import { Sparkles } from 'lucide-react';

const statusStyles: Record<string, string> = {
  'In Stock': 'bg-green-50 text-green-800 before:bg-green-600 dark:bg-green-900/30 dark:text-green-200 dark:before:bg-green-400',
  'Low Stock': 'bg-orange-50 text-orange-800 before:bg-orange-600 dark:bg-orange-900/30 dark:text-orange-200 dark:before:bg-orange-400',
  'Out of Stock': 'bg-red-50 text-red-800 before:bg-red-600 dark:bg-red-900/30 dark:text-red-200 dark:before:bg-red-400',
  Draft: 'bg-canvas-soft text-ink-muted',
  'Pending Approval': 'bg-orange-50 text-orange-800 dark:bg-orange-900/30 dark:text-orange-200',
  Approved: 'bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-200',
  Sent: 'bg-brand-50 text-brand-800 dark:bg-brand-900/30 dark:text-brand-200',
  Confirmed: 'bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-200',
  Rejected: 'bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-200',
  'AI Generated': 'bg-purple-50 text-purple-800 dark:bg-purple-900/30 dark:text-purple-200',
  Viewer: 'bg-canvas-soft text-ink-muted',
  Manager: 'bg-brand-50 text-brand-800 dark:bg-brand-900/30 dark:text-brand-200',
  Admin: 'bg-purple-50 text-purple-800 dark:bg-purple-900/30 dark:text-purple-200',
  Active: 'bg-green-50 text-green-800 before:bg-green-600 dark:bg-green-900/30 dark:text-green-200 dark:before:bg-green-400',
  Inactive: 'bg-canvas-soft text-ink-muted',
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
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-eyebrow bg-canvas-soft text-ink-muted">
        {children}
      </span>
    );
  }

  const hasDot = showDot && classes.includes('before:');

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-eyebrow ${classes} ${
        hasDot ? 'before:content-[""] before:w-1.5 before:h-1.5 before:rounded-full before:shrink-0' : ''
      }`}
    >
      {isAi && <Sparkles className="w-3 h-3" />}
      {children}
    </span>
  );
}
