import type { Decorator } from '@storybook/react-vite';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore, type User, type Role } from '../../store/authStore';
import { useToastStore } from '../../store/toastStore';

export const withRouter: Decorator = (Story) => (
  <MemoryRouter initialEntries={['/']}>
    <Story />
  </MemoryRouter>
);

export const withQueryClient: Decorator = (Story) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return (
    <QueryClientProvider client={queryClient}>
      <Story />
    </QueryClientProvider>
  );
};

export const withMockAuth: Decorator = (Story, context) => {
  const mockUser: User = {
    id: 1,
    email: 'admin@smartstock.ai',
    name: 'Admin User',
    role: (context.parameters?.authRole as Role) ?? 'admin',
    is_active: true,
  };
  useAuthStore.setState({
    user: mockUser,
    token: 'mock-token',
    refreshToken: 'mock-refresh',
    isBootstrapping: false,
  });
  return <Story />;
};

export function setupToastStories() {
  const store = useToastStore.getState();
  store.toasts.forEach((t) => store.removeToast(t.id));
  return store;
}

export const withToast: Decorator = (Story) => {
  const store = useToastStore.getState();
  store.toasts.forEach((t) => store.removeToast(t.id));
  return <Story />;
};
