import api from '../../lib/axios';
import type { CreateUserPayload, UpdateUserRolePayload, User } from './types';

export async function listUsers(): Promise<User[]> {
  const { data } = await api.get<{ results?: User[]; count?: number } | User[]>('/auth/users/');
  if (Array.isArray(data)) return data;
  return data.results ?? [];
}

export async function createUser(payload: CreateUserPayload): Promise<User> {
  const { data } = await api.post<User>('/auth/users/', payload);
  return data;
}

export async function updateUserRole(id: number, payload: UpdateUserRolePayload): Promise<User> {
  const { data } = await api.patch<User>(`/auth/users/${id}/`, payload);
  return data;
}

export async function deactivateUser(id: number): Promise<User> {
  const { data } = await api.delete<User>(`/auth/users/${id}/`);
  return data;
}
