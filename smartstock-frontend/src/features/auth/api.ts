import axios from 'axios';
import api from '../../lib/axios';
import type { LoginPayload, LoginResponse, RegisterPayload } from './types';

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login/', payload);
  return data;
}

export async function register(payload: RegisterPayload): Promise<{ detail: string }> {
  const { data } = await api.post<{ detail: string }>('/auth/register/', payload);
  return data;
}

export async function logout(): Promise<void> {
  try {
    await api.post(
      '/auth/logout/',
      {},
      { withCredentials: true },
    );
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      return;
    }
    throw err;
  }
}

export async function verifyEmail(token: string): Promise<{ detail: string }> {
  const { data } = await api.post<{ detail: string }>('/auth/verify-email/', { token });
  return data;
}

export async function resendVerification(email: string): Promise<{ detail: string }> {
  const { data } = await api.post<{ detail: string }>('/auth/resend-verification/', { email });
  return data;
}
