import type { LoginResponse, Role, User } from './types';

declare global {
  interface Window {
    __ENV__?: Record<string, string>;
  }
}

const env = window.__ENV__ ?? {};
const FLAG = env.VITE_AUTH_BYPASS ?? import.meta.env.VITE_AUTH_BYPASS ?? '';

export const devBypass = {
  enabled: FLAG === 'true' || FLAG === '1',
} as const;

const NAME_BY_ROLE: Record<Role, string> = {
  viewer: 'Demo Viewer',
  manager: 'Demo Manager',
  admin: 'Demo Admin',
};

const EMAIL_BY_ROLE: Record<Role, string> = {
  viewer: 'demo.viewer@smartstock.local',
  manager: 'demo.manager@smartstock.local',
  admin: 'demo.admin@smartstock.local',
};

export function buildMockSession(role: Role): LoginResponse {
  const user: User = {
    id: role === 'admin' ? 1 : role === 'manager' ? 2 : 3,
    email: EMAIL_BY_ROLE[role],
    name: NAME_BY_ROLE[role],
    role,
  };
  return {
    access: `dev-bypass.${role}.${Date.now()}`,
    user,
  };
}
