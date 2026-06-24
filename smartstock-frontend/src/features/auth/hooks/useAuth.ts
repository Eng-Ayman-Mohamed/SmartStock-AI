import { useCallback, useMemo, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../../store/authStore';
import * as authApi from '../api';
import type { LoginPayload, RegisterPayload } from '../types';

export type AuthError = { kind: 'invalid_credentials' | 'email_not_verified' | 'network' | 'validation' | 'already_exists' | 'unknown'; message: string; fields?: Record<string, string[]> };

function toAuthError(err: unknown): AuthError {
  if (axios.isAxiosError(err)) {
    if (!err.response) {
      return { kind: 'network', message: "Can't reach the server. Check your connection and try again." };
    }
    const data = err.response.data as Record<string, unknown> | undefined;
    if (err.response.status === 403 && data?.error === 'EmailNotVerified') {
      return { kind: 'email_not_verified', message: (data.message as string) || 'Please verify your email before logging in.' };
    }
    if (err.response.status === 409) {
      return {
        kind: 'already_exists',
        message: (data?.message as string) || 'An account with this email already exists. Check your email for the verification link, or resend it.',
      };
    }
    if (err.response.status === 401 || err.response.status === 400) {
      return { kind: 'invalid_credentials', message: 'Invalid email or password.' };
    }
    if (err.response.status === 422) {
      const rawData = err.response.data as Record<string, unknown> | undefined;
      const fields = (rawData?.fields as Record<string, string[]>) || (rawData as Record<string, string[]>) || {};
      return { kind: 'validation', message: 'Please fix the errors below.', fields };
    }
    return { kind: 'unknown', message: 'Something went wrong. Please try again.' };
  }
  return { kind: 'unknown', message: 'Something went wrong. Please try again.' };
}

export function useAuth() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  const isBootstrapping = useAuthStore((s) => s.isBootstrapping);
  const setToken = useAuthStore((s) => s.setToken);
  const setRefreshToken = useAuthStore((s) => s.setRefreshToken);
  const setUser = useAuthStore((s) => s.setUser);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);

  const isAuthenticated = useMemo(() => Boolean(token && user), [token, user]);

  const login = useCallback(
    async (payload: LoginPayload, redirectTo: string = '/dashboard') => {
      setError(null);
      setIsSubmitting(true);
      try {
        const res = await authApi.login(payload);
        setToken(res.access);
        setRefreshToken(res.refresh);
        setUser(res.user);
        navigate(redirectTo, { replace: true });
      } catch (err) {
        setError(toAuthError(err));
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    [navigate, setToken, setRefreshToken, setUser],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      setError(null);
      setIsSubmitting(true);
      try {
        await authApi.register(payload);
      } catch (err) {
        setError(toAuthError(err));
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (err) {
      console.warn('Logout request failed; clearing local session anyway.', err);
    } finally {
      clearAuth();
      navigate('/login', { replace: true });
    }
  }, [clearAuth, navigate]);

  return {
    user,
    token,
    isAuthenticated,
    isBootstrapping,
    isSubmitting,
    error,
    login,
    register,
    logout,
    clearError: () => setError(null),
  };
}
