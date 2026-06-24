import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate, type Location } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { resendVerification } from '../api';
import Button from '../../../shared/components/Button';
import PasswordField from '../../../shared/components/PasswordField';

type LocationState = { from?: Location };

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginForm() {
  const { login, isSubmitting, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);

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
    const fromPath = state?.from?.pathname ?? '/dashboard';
    const redirectTo = fromPath === '/login' || fromPath === '/register' ? '/dashboard' : fromPath;
    await login({ email: email.trim(), password }, redirectTo);
  }

  async function handleResend() {
    if (!email.trim()) return;
    setResending(true);
    try {
      await resendVerification(email.trim());
      setResent(true);
    } catch {
      // Silently ignore — we don't want to leak whether the email exists
    } finally {
      setResending(false);
    }
  }

  return (
    <form noValidate onSubmit={onSubmit} className="space-y-5" aria-describedby={error ? formErrorId : undefined}>
      <div>
        <label htmlFor="email" className="block text-caption font-medium text-ink mb-1.5">
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
          className="w-full h-9 px-3 rounded-md border border-hairline bg-canvas text-body text-ink placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
          placeholder="you@company.com"
        />
        {fieldErrors.email && (
          <p id={emailErrId} className="mt-1 text-caption text-red-600">
            {fieldErrors.email}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-caption font-medium text-ink mb-1.5">
          Password
        </label>
        <PasswordField
          id="password"
          name="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            if (fieldErrors.password) setFieldErrors((p) => ({ ...p, password: undefined }));
          }}
          error={Boolean(fieldErrors.password)}
          aria-describedby={fieldErrors.password ? passwordErrId : undefined}
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
          <p>{error.message}</p>
          {error.kind === 'email_not_verified' && !resent && (
            <button
              type="button"
              onClick={handleResend}
              disabled={resending}
              className="mt-2 text-brand-600 hover:text-brand-800 font-medium underline"
            >
              {resending ? 'Sending...' : 'Resend verification email'}
            </button>
          )}
          {resent && (
            <p className="mt-2 text-green-700">Verification email sent. Check your inbox.</p>
          )}
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

      <p className="text-center text-caption text-ink-muted">
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
