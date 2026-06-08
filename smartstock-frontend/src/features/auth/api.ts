import axios from 'axios';
import api from '../../lib/axios';
import type { LoginPayload, LoginResponse, RegisterPayload, User } from './types';

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/login/', payload);
  return data;
}

export async function register(payload: RegisterPayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/auth/register/', payload);
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

export async function me(): Promise<User> {
  const { data } = await api.get<User>('/auth/me/');
  return data;
}
