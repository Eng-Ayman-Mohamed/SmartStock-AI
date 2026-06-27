import type { Meta, StoryObj } from '@storybook/react-vite';
import LoginForm from './LoginForm';
import { useAuthStore } from '../../../store/authStore';

const meta = {
  title: 'Auth/LoginForm',
  component: LoginForm,
  tags: ['autodocs'],
  decorators: [
    (Story) => {
      useAuthStore.setState({
        user: null,
        token: null,
        refreshToken: null,
        isBootstrapping: false,
      });
      return <Story />;
    },
  ],
} satisfies Meta<typeof LoginForm>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
