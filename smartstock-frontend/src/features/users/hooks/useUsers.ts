import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../../store/authStore';
import * as usersApi from '../api';
import type { CreateUserPayload, UpdateUserRolePayload } from '../types';

export const usersQueryKey = ['users'] as const;

const orderingMap: Record<string, string> = {
  name: 'first_name',
  role: 'role',
  status: 'is_active',
  joined: 'date_joined',
};

export function useUsers(
  searchQuery?: string,
  page: number = 1,
  pageSize: number = 20,
  isActive?: boolean,
  sortField?: string,
  sortOrder?: string,
) {
  const token = useAuthStore((s) => s.token);
  const ordering = sortField
    ? sortOrder === 'desc'
      ? `-${orderingMap[sortField] ?? sortField}`
      : (orderingMap[sortField] ?? sortField)
    : '';
  return useQuery({
    queryKey: [...usersQueryKey, page, pageSize, searchQuery, isActive, sortField, sortOrder],
    queryFn: () => usersApi.listUsers(page, pageSize, searchQuery ?? '', isActive, ordering),
    enabled: !!token,
    retry: false,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateUserPayload) => usersApi.createUser(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: usersQueryKey });
    },
  });
}

export function useUpdateUserRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, role }: { id: number; role: UpdateUserRolePayload['role'] }) =>
      usersApi.updateUserRole(id, { role }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: usersQueryKey });
    },
  });
}

export function useDeactivateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => usersApi.deactivateUser(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: usersQueryKey });
    },
  });
}
