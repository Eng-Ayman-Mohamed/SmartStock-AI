import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate, type Location } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import Button from '../../../shared/components/Button';

type LocationState = { from?: Location };

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginForm() {
  const { login, isSubmitting, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  const formErrorId = 'login-form-error';
  const emailErrId = 'login-email-error';
  const passwordErrId = 'login-password-error';

  function validate(): boolean {
    const next: { email?: string; password?: string } = {};
    if (!email.trim()) {
      next.email = 'Email is required.';
    } else if (!EMAIL_RE.test(email.trim())) {
      next.email = 'Enter a valid email address.';
    }
    if (!password) {
      next.password = 'Password is required.';
    }
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    clearError();
    if (!validate()) return;

    const state = (location.state as LocationState | null) ?? null;
    const fromPath = state?.from?.pathname ?? '/';
    const redirectTo = fromPath === '/login' || fromPath === '/register' ? '/' : fromPath;
    await login({ email: email.trim(), password }, redirectTo);
  }

  return (
    <form noValidate onSubmit={onSubmit} className="space-y-5" aria-describedby={error ? formErrorId : undefined}>
      <div>
        <label htmlFor="email" className="block text-caption font-medium text-gray-900 mb-1.5">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: undefined }));
          }}
          aria-invalid={Boolean(fieldErrors.email)}
          aria-describedby={fieldErrors.email ? emailErrId : undefined}
          className="w-full h-9 px-3 rounded-md border border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
          placeholder="you@company.com"
        />
        {fieldErrors.email && (
          <p id={emailErrId} className="mt-1 text-caption text-red-600">
            {fieldErrors.email}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-caption font-medium text-gray-900 mb-1.5">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            if (fieldErrors.password) setFieldErrors((p) => ({ ...p, password: undefined }));
          }}
          aria-invalid={Boolean(fieldErrors.password)}
          aria-describedby={fieldErrors.password ? passwordErrId : undefined}
          className="w-full h-9 px-3 rounded-md border border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
          placeholder="••••••••"
        />
        {fieldErrors.password && (
          <p id={passwordErrId} className="mt-1 text-caption text-red-600">
            {fieldErrors.password}
          </p>
        )}
      </div>

      {error && (
        <div
          id={formErrorId}
          role="alert"
          className="rounded-md border border-red-100 bg-red-50 px-3 py-2 text-caption text-red-600"
        >
          {error.message}
        </div>
      )}

      <Button type="submit" variant="primary" size="lg" disabled={isSubmitting} className="w-full">
        {isSubmitting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            <span>Signing in…</span>
          </>
        ) : (
          <span>Sign in</span>
        )}
      </Button>

      <p className="text-center text-caption text-gray-600">
        Don't have an account?{' '}
        <button
          type="button"
          onClick={() => navigate('/register')}
          className="text-brand-600 hover:text-brand-800 font-medium"
        >
          Create one
        </button>
      </p>
    </form>
  );
}
