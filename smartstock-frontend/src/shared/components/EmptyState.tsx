import type { LucideIcon } from 'lucide-react';
import Button from './Button';

interface EmptyStateProps {
  icon: LucideIcon;
  heading: string;
  body: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({ icon: Icon, heading, body, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <Icon className="w-12 h-12 text-gray-300 mb-4" aria-hidden="true" />
      <h3 className="text-card-title text-gray-700 mb-1">{heading}</h3>
      <p className="text-body text-gray-500 text-center max-w-[280px] mb-4">{body}</p>
      {actionLabel && onAction && (
        <Button size="md" onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}
