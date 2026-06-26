import type { Meta, StoryObj } from '@storybook/react-vite';
import Header from './Header';
import { withRouter } from '../test-utils/decorators';
import { useAuthStore } from '../../store/authStore';

const mockUser = {
  id: 1,
  email: 'admin@smartstock.ai',
  name: 'Admin User',
  role: 'admin' as const,
  is_active: true,
};

const meta = {
  title: 'Layout/Header',
  component: Header,
  tags: ['autodocs'],
  decorators: [
    withRouter,
    (Story) => {
      useAuthStore.setState({
        user: mockUser,
        token: 'mock-token',
        refreshToken: 'mock-refresh',
        isBootstrapping: false,
      });
      return <Story />;
    },
  ],
} satisfies Meta<typeof Header>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
