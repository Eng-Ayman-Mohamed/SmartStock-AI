import type { ReactNode } from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  noPadding?: boolean;
  fillHeight?: boolean;
}

export default function Card({ title, subtitle, action, children, className = '', noPadding = false, fillHeight = false }: CardProps) {
  return (
    <div className={`bg-canvas border border-hairline rounded-lg flex flex-col ${noPadding ? 'flex-1 min-h-0' : ''} ${fillHeight ? 'flex-1 min-h-0' : ''} ${className}`}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-2 px-4 sm:px-6 pt-4 sm:pt-6 pb-4 border-b border-hairline shrink-0">
          <div className="min-w-0">
            {title && <h3 className="text-card-title text-ink">{title}</h3>}
            {subtitle && <p className="text-caption text-ink-muted mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      <div className={`${noPadding ? 'min-w-0 flex-1 min-h-0 flex flex-col' : fillHeight ? 'p-4 sm:p-6 min-w-0 flex-1 min-h-0 flex flex-col' : 'p-4 sm:p-6 min-w-0'}`}>
        {children}
      </div>
    </div>
  );
}
