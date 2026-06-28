import { forwardRef, type InputHTMLAttributes } from 'react';

type InputVariant = 'default' | 'error';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  variant?: InputVariant;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({ variant = 'default', className, ...props }, ref) => {
  const base = 'w-full h-11 px-3 rounded-md border bg-canvas text-body text-ink placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors';
  const border = variant === 'error' ? 'border-red-300' : 'border-hairline hover:border-ink-muted';

  return (
    <input
      ref={ref}
      className={`${base} ${border} ${className ?? ''}`}
      {...props}
    />
  );
});

Input.displayName = 'Input';

export default Input;
