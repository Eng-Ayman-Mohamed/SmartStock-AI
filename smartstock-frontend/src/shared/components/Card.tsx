import type { ReactNode } from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  noPadding?: boolean;
}

export default function Card({ title, subtitle, action, children, className = '', noPadding = false }: CardProps) {
  return (
    <div className={`bg-canvas border border-hairline rounded-lg ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-hairline">
          <div>
            {title && <h3 className="text-card-title text-ink">{title}</h3>}
            {subtitle && <p className="text-caption text-ink-muted mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={noPadding ? '' : 'p-6'}>
        {children}
      </div>
    </div>
  );
}
