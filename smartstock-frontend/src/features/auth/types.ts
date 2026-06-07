import type { Role, User } from '../../store/authStore';

export type { Role, User };

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh?: string;
  user: User;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface FieldErrors {
  [field: string]: string[];
}

export interface ApiErrorPayload {
  [field: string]: string[] | string;
}
