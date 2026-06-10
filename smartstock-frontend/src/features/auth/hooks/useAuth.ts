import { useCallback, useMemo, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../../store/authStore';
import * as authApi from '../api';
import type { LoginPayload, RegisterPayload } from '../types';

export type AuthError = { kind: 'invalid_credentials' | 'network' | 'unknown'; message: string };

function toAuthError(err: unknown): AuthError {
  if (axios.isAxiosError(err)) {
    if (!err.response) {
      return { kind: 'network', message: "Can't reach the server. Check your connection and try again." };
    }
    if (err.response.status === 401 || err.response.status === 400) {
      return { kind: 'invalid_credentials', message: 'Invalid email or password.' };
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
  const setUser = useAuthStore((s) => s.setUser);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);

  const isAuthenticated = useMemo(() => Boolean(token && user), [token, user]);

  const login = useCallback(
    async (payload: LoginPayload, redirectTo: string = '/') => {
      setError(null);
      setIsSubmitting(true);
      try {
        const res = await authApi.login(payload);
        setToken(res.access);
        setUser(res.user);
        navigate(redirectTo, { replace: true });
      } catch (err) {
        setError(toAuthError(err));
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    [navigate, setToken, setUser],
  );

  const register = useCallback(
    async (payload: RegisterPayload, redirectTo: string = '/') => {
      setError(null);
      setIsSubmitting(true);
      try {
        const res = await authApi.register(payload);
        setToken(res.access);
        setUser(res.user);
        navigate(redirectTo, { replace: true });
      } catch (err) {
        setError(toAuthError(err));
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    [navigate, setToken, setUser],
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
