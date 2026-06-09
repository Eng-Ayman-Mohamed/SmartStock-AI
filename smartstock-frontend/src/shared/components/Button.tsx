import type { ButtonHTMLAttributes, ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'utility';
type Size = 'sm' | 'md' | 'lg';

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-brand-600 text-white hover:bg-brand-800 disabled:bg-canvas-soft disabled:text-ink-faint ' +
    'rounded-full',
  secondary:
    'bg-canvas border border-hairline text-ink hover:bg-canvas-soft disabled:bg-canvas-soft disabled:text-ink-faint disabled:border-hairline ' +
    'shadow-soft rounded-full',
  danger:
    'bg-red-600 text-white hover:bg-red-800 disabled:bg-canvas-soft disabled:text-ink-faint ' +
    'rounded-full',
  ghost:
    'bg-transparent text-brand-600 hover:bg-brand-50 disabled:text-ink-faint disabled:hover:bg-transparent ' +
    'rounded-full',
  utility:
    'bg-canvas border border-hairline text-ink hover:bg-canvas-soft disabled:bg-canvas-soft disabled:text-ink-faint ' +
    'rounded-full',
};

const sizeClasses: Record<Size, string> = {
  sm: 'h-7 px-3 py-1.5 text-body',
  md: 'h-9 px-4 py-2 text-body',
  lg: 'h-11 px-5 py-2.5 text-body',
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
}

export default function Button({ variant = 'primary', size = 'md', className = '', children, ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 font-medium transition-all duration-150 cursor-pointer disabled:cursor-not-allowed active:scale-[0.97] ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
