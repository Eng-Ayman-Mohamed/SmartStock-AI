import { useState, type FormEvent } from 'react';
import { Loader2, X } from 'lucide-react';
import { useCreateUser } from '../hooks/useUsers';
import { ROLE_META } from './RoleBadge';
import type { Role } from '../types';
import { useAuthStore } from '../../../store/authStore';

interface InviteUserModalProps {
  open: boolean;
  onClose: () => void;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;
const ROLES: Role[] = ['viewer', 'manager', 'admin'];

export default function InviteUserModal({ open, onClose }: InviteUserModalProps) {
  const createUser = useCreateUser();
  const currentUserId = useAuthStore((s) => s.user?.id);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>('viewer');
  const [fieldErrors, setFieldErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
  }>({});
  const [formError, setFormError] = useState<string | null>(null);

  if (!open) return null;

  function reset() {
    setName('');
    setEmail('');
    setPassword('');
    setRole('viewer');
    setFieldErrors({});
    setFormError(null);
  }

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFieldErrors({});
    setFormError(null);

    const next: typeof fieldErrors = {};
    if (!name.trim()) next.name = 'Name is required.';
    if (!email.trim()) next.email = 'Email is required.';
    else if (!EMAIL_RE.test(email.trim())) next.email = 'Enter a valid email address.';
    if (!password) next.password = 'Password is required.';
    else if (password.length < MIN_PASSWORD_LENGTH)
      next.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;

    if (Object.keys(next).length > 0) {
      setFieldErrors(next);
      return;
    }

    createUser.mutate(
      { name: name.trim(), email: email.trim(), password, role },
      {
        onSuccess: () => {
          reset();
          onClose();
        },
        onError: (err: unknown) => {
          setFormError('Could not create user. The email may already be in use.');
          console.error('create user failed', err, 'currentUserId=', currentUserId);
        },
      },
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-labelledby="invite-user-title"
    >
      <div className="w-full max-w-[460px] bg-white rounded-lg border border-gray-100 shadow-xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 id="invite-user-title" className="text-card-title font-semibold text-gray-900">
            Invite user
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="flex items-center justify-center w-7 h-7 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-50"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={onSubmit} className="px-5 py-4 space-y-4">
          <div>
            <label htmlFor="invite-name" className="block text-caption font-medium text-gray-900 mb-1.5">
              Full name
            </label>
            <input
              id="invite-name"
              type="text"
              autoComplete="name"
              required
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (fieldErrors.name) setFieldErrors((p) => ({ ...p, name: undefined }));
              }}
              aria-invalid={Boolean(fieldErrors.name)}
              className="w-full h-9 px-3 rounded-md border border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
              placeholder="Jane Doe"
            />
            {fieldErrors.name && (
              <p className="mt-1 text-caption text-red-600">{fieldErrors.name}</p>
            )}
          </div>

          <div>
            <label htmlFor="invite-email" className="block text-caption font-medium text-gray-900 mb-1.5">
              Email
            </label>
            <input
              id="invite-email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: undefined }));
              }}
              aria-invalid={Boolean(fieldErrors.email)}
              className="w-full h-9 px-3 rounded-md border border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
              placeholder="user@company.com"
            />
            {fieldErrors.email && (
              <p className="mt-1 text-caption text-red-600">{fieldErrors.email}</p>
            )}
          </div>

          <div>
            <label htmlFor="invite-password" className="block text-caption font-medium text-gray-900 mb-1.5">
              Temporary password
            </label>
            <input
              id="invite-password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (fieldErrors.password) setFieldErrors((p) => ({ ...p, password: undefined }));
              }}
              aria-invalid={Boolean(fieldErrors.password)}
              className="w-full h-9 px-3 rounded-md border border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-100 focus:border-brand-600 transition-colors"
              placeholder="At least 8 characters"
            />
            {fieldErrors.password && (
              <p className="mt-1 text-caption text-red-600">{fieldErrors.password}</p>
            )}
            <p className="mt-1 text-caption text-gray-600">
              Share this with the user. They can change it after first login.
            </p>
          </div>

          <div>
            <span className="block text-caption font-medium text-gray-900 mb-1.5">Role</span>
            <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Role">
              {ROLES.map((r) => {
                const meta = ROLE_META[r];
                const isSelected = r === role;
                return (
                  <button
                    key={r}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    onClick={() => setRole(r)}
                    className={`px-3 py-2 rounded-md border text-caption font-medium text-left transition-colors ${
                      isSelected
                        ? 'border-brand-600 bg-brand-50 text-brand-800'
                        : 'border-gray-100 bg-white text-gray-700 hover:border-gray-200'
                    }`}
                  >
                    <span className="block capitalize">{meta.label}</span>
                    <span className="block text-caption text-gray-500 mt-0.5">
                      {r === 'viewer' && 'Read-only'}
                      {r === 'manager' && 'Approvals + edits'}
                      {r === 'admin' && 'Full access'}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {formError && (
            <div role="alert" className="rounded-md border border-red-100 bg-red-50 px-3 py-2 text-caption text-red-600">
              {formError}
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 h-9 rounded-md text-caption font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createUser.isPending}
              className="inline-flex items-center justify-center gap-2 h-9 px-4 rounded-md bg-brand-600 text-white text-caption font-medium hover:bg-brand-800 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
            >
              {createUser.isPending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                  <span>Creating…</span>
                </>
              ) : (
                <span>Send invite</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
