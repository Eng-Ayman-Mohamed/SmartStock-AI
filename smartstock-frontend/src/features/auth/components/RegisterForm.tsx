import { useState, type FormEvent } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import Button from '../../../shared/components/Button';
import type { ApiErrorPayload } from '../types';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;

type Fields = { name?: string; email?: string; password?: string; confirm?: string };

function readError(value: string[] | string | undefined): string | undefined {
  if (!value) return undefined;
  if (Array.isArray(value)) return value[0];
  return value;
}

export default function RegisterForm() {
  const { register, isSubmitting, error, clearError } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Fields>({});

  const formErrorId = 'register-form-error';
  const nameErrId = 'register-name-error';
  const emailErrId = 'register-email-error';
  const passwordErrId = 'register-password-error';
  const confirmErrId = 'register-confirm-error';

  function validate(): boolean {
    const next: Fields = {};
    if (!name.trim()) {
      next.name = 'Name is required.';
    }
    if (!email.trim()) {
      next.email = 'Email is required.';
    } else if (!EMAIL_RE.test(email.trim())) {
      next.email = 'Enter a valid email address.';
    }
    if (!password) {
      next.password = 'Password is required.';
    } else if (password.length < MIN_PASSWORD_LENGTH) {
      next.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
    }
    if (!confirm) {
      next.confirm = 'Please confirm your password.';
    } else if (confirm !== password) {
      next.confirm = 'Passwords do not match.';
    }
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  }

  function pickServerErrors(err: unknown): Fields {
    if (axios.isAxiosError(err) && err.response?.data) {
      const data = err.response.data as ApiErrorPayload;
      const out: Fields = {};
      const nameErr = readError(data.name);
      const emailErr = readError(data.email);
      const passwordErr = readError(data.password);
      if (nameErr) out.name = nameErr;
      if (emailErr) out.email = emailErr;
      if (passwordErr) out.password = passwordErr;
      return out;
    }
    return {};
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    clearError();
    setFieldErrors({});
    if (!validate()) return;

    try {
      await register({ name: name.trim(), email: email.trim(), password }, '/');
    } catch (err) {
      const serverErrors = pickServerErrors(err);
      if (Object.keys(serverErrors).length > 0) {
        setFieldErrors(serverErrors);
      }
    }
  }

  return (
    <form noValidate onSubmit={onSubmit} className="space-y-5" aria-describedby={error ? formErrorId : undefined}>
      <div>
        <label htmlFor="name" className="block text-caption font-medium text-gray-900 mb-1.5">
          Full name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          autoComplete="name"
          required
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            if (fieldErrors.name) setFieldErrors((p) => ({ ...p, name: undefined }));
          }}
          aria-invalid={Boolean(fieldErrors.name)}
          aria-describedby={fieldErrors.name ? nameErrId : undefined}
          className="w-full h-9 px-3 rounded-md border border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
          placeholder="Jane Doe"
        />
        {fieldErrors.name && (
          <p id={nameErrId} className="mt-1 text-caption text-red-600">
            {fieldErrors.name}
          </p>
        )}
      </div>

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
          autoComplete="new-password"
          required
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            if (fieldErrors.password) setFieldErrors((p) => ({ ...p, password: undefined }));
          }}
          aria-invalid={Boolean(fieldErrors.password)}
          aria-describedby={fieldErrors.password ? passwordErrId : undefined}
          className="w-full h-9 px-3 rounded-md border border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
          placeholder="At least 8 characters"
        />
        {fieldErrors.password && (
          <p id={passwordErrId} className="mt-1 text-caption text-red-600">
            {fieldErrors.password}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="confirm" className="block text-caption font-medium text-gray-900 mb-1.5">
          Confirm password
        </label>
        <input
          id="confirm"
          name="confirm"
          type="password"
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => {
            setConfirm(e.target.value);
            if (fieldErrors.confirm) setFieldErrors((p) => ({ ...p, confirm: undefined }));
          }}
          aria-invalid={Boolean(fieldErrors.confirm)}
          aria-describedby={fieldErrors.confirm ? confirmErrId : undefined}
          className="w-full h-9 px-3 rounded-md border border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
          placeholder="Repeat password"
        />
        {fieldErrors.confirm && (
          <p id={confirmErrId} className="mt-1 text-caption text-red-600">
            {fieldErrors.confirm}
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
            <span>Creating account…</span>
          </>
        ) : (
          <span>Create account</span>
        )}
      </Button>

      <p className="text-center text-caption text-gray-600">
        Already have an account?{' '}
        <button
          type="button"
          onClick={() => navigate('/login')}
          className="text-brand-600 hover:text-brand-800 font-medium"
        >
          Sign in
        </button>
      </p>
    </form>
  );
}
