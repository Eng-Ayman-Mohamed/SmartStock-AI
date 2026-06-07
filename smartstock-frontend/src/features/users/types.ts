import type { Role } from '../auth/types';

export type { Role };

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface CreateUserPayload {
  name: string;
  email: string;
  password: string;
  role: Role;
}

export interface UpdateUserRolePayload {
  role: Role;
}

export type StatusFilter = 'all' | 'active' | 'deactivated';
