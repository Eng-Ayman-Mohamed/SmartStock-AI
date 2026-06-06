import { create } from 'zustand';

export interface User {
  id: number;
  email: string;
  name: string;
  role: 'viewer' | 'manager' | 'admin';
}

interface AuthState {
  user: User | null;
  token: string | null;
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  setToken: (token) => set({ token }),
  setUser: (user) => set({ user }),
  clearAuth: () => set({ user: null, token: null }),
}));
