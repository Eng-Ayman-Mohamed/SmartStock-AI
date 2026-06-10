import { create } from 'zustand';
import api from '../lib/axios';

export type Role = 'viewer' | 'manager' | 'admin';

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isBootstrapping: boolean;
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  setBootstrapping: (value: boolean) => void;
  clearAuth: () => void;
  bootstrapSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isBootstrapping: true,

  setToken: (token) => set({ token }),
  setUser: (user) => set({ user }),
  setBootstrapping: (value) => set({ isBootstrapping: value }),
  clearAuth: () => set({ user: null, token: null }),

  bootstrapSession: async () => {
    if (!get().isBootstrapping) return;
    set({ isBootstrapping: true });
    try {
      const { data: refreshData } = await api.post<{ access: string }>(
        '/auth/refresh/',
        {},
        { withCredentials: true },
      );
      if (refreshData?.access) {
        set({ token: refreshData.access });
        try {
          const { data: me } = await api.get<{ id: number; email: string; name: string; role: Role }>(
            '/auth/me/',
          );
          set({ user: me });
        } catch {
          set({ user: null });
        }
      }
    } catch {
      set({ user: null, token: null });
    } finally {
      set({ isBootstrapping: false });
    }
  },
}));
