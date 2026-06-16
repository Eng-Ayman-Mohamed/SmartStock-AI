import { useState, useId, type InputHTMLAttributes } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface PasswordFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  error?: boolean;
}

export default function PasswordField({ error, className, id: idProp, ...rest }: PasswordFieldProps) {
  const [visible, setVisible] = useState(false);
  const autoId = useId();
  const id = idProp ?? autoId;
  return (
    <div className="relative">
      <input
        id={id}
        type={visible ? 'text' : 'password'}
        aria-invalid={error || undefined}
        className={`w-full h-9 px-3 pr-9 rounded-md border bg-canvas text-body text-ink placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors ${error ? 'border-red-300' : 'border-hairline'} ${className ?? ''}`}
        {...rest}
      />
      <button
        type="button"
        tabIndex={-1}
        aria-label={visible ? 'Hide password' : 'Show password'}
        onClick={() => setVisible((v) => !v)}
        className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded text-ink-faint hover:text-ink-muted"
      >
        {visible ? (
          <EyeOff className="w-4 h-4" aria-hidden="true" />
        ) : (
          <Eye className="w-4 h-4" aria-hidden="true" />
        )}
      </button>
    </div>
  );
}
