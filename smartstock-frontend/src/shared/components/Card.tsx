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
    <div className={`bg-white border-[0.5px] border-gray-100 rounded-lg ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b-[0.5px] border-gray-100">
          <div>
            {title && <h3 className="text-card-title text-gray-900">{title}</h3>}
            {subtitle && <p className="text-caption text-gray-600 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={noPadding ? '' : 'p-5'}>
        {children}
      </div>
    </div>
  );
}
