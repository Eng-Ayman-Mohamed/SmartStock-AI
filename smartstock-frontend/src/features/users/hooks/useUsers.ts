import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../../store/authStore';
import * as usersApi from '../api';
import type { CreateUserPayload, UpdateUserRolePayload } from '../types';

export const usersQueryKey = ['users'] as const;

export function useUsers() {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: usersQueryKey,
    queryFn: usersApi.listUsers,
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
