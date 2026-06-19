import api from '../../lib/axios';
import type { CreateUserPayload, UpdateUserRolePayload, User } from './types';

export async function listUsers(
  page: number = 1,
  pageSize: number = 20,
  search: string = '',
  isActive?: boolean,
): Promise<PaginatedResponse<User>> {
  const params: Record<string, string | number | boolean | undefined> = {
    page,
    page_size: pageSize,
    search: search || undefined,
  };
  if (isActive !== undefined) {
    params.is_active = isActive;
  }
  const { data } = await api.get<PaginatedResponse<User>>('/auth/users/', { params });
  return data;
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
