import { forwardRef, type SelectHTMLAttributes } from 'react';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  variant?: 'default' | 'error';
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(({ variant = 'default', className, children, ...props }, ref) => {
  const base = 'w-full h-11 px-3 pr-8 rounded-md border bg-canvas text-body text-ink focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors appearance-none bg-[url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20width%3D%2712%27%20height%3D%2712%27%20viewBox%3D%270%200%2024%2024%27%20fill%3D%27none%27%20stroke%3D%27%23A39E98%27%20stroke-width%3D%272%27%20stroke-linecap%3D%27round%27%20stroke-linejoin%3D%27round%27%3E%3Cpath%20d%3D%27m6%209%206%206%206-6%27%2F%3E%3C%2Fsvg%3E")] bg-[length:12px] bg-[right_12px_center] bg-no-repeat';
  const border = variant === 'error' ? 'border-red-300' : 'border-hairline hover:border-ink-muted';

  return (
    <select
      ref={ref}
      className={`${base} ${border} ${className ?? ''}`}
      {...props}
    >
      {children}
    </select>
  );
});

Select.displayName = 'Select';

export default Select;
