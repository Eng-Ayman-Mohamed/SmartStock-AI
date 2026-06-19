import { create } from 'zustand';
import api from '../lib/axios';

export type Role = 'viewer' | 'manager' | 'admin';

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  is_active?: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isBootstrapping: boolean;
  setToken: (token: string | null) => void;
  setRefreshToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  setBootstrapping: (value: boolean) => void;
  clearAuth: () => void;
  bootstrapSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  refreshToken: null,
  isBootstrapping: true,

  setToken: (token) => set({ token }),
  setRefreshToken: (refreshToken) => set({ refreshToken }),
  setUser: (user) => set({ user }),
  setBootstrapping: (value) => set({ isBootstrapping: value }),
  clearAuth: () => {
    set({ user: null, token: null, refreshToken: null });
  },

  bootstrapSession: async () => {
    if (!get().isBootstrapping) return;
    set({ isBootstrapping: true });
    try {
      const { data: refreshData } = await api.post<{ access: string; refresh?: string }>(
        '/auth/refresh/',
        {},
        { withCredentials: true },
      );
      if (refreshData?.access) {
        set({ token: refreshData.access });
        if (refreshData.refresh) {
          set({ refreshToken: refreshData.refresh });
        }
        try {
          const { data: me } = await api.get<{ id: number; email: string; name: string; role: Role }>(
            '/auth/me/',
          );
          set({ user: me });
        } catch {
          console.warn('Bootstrap: /auth/me/ failed');
          set({ user: null });
        }
      }
    } catch {
      if (import.meta.env.DEV) {
        console.debug('Bootstrap: refresh failed');
      }
      set({ user: null, token: null, refreshToken: null });
    } finally {
      set({ isBootstrapping: false });
    }
  },
}));
