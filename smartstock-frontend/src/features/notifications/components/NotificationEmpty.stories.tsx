import type { Meta, StoryObj } from '@storybook/react-vite';
import NotificationEmpty from './NotificationEmpty';

const meta = {
  title: 'Notifications/NotificationEmpty',
  component: NotificationEmpty,
  tags: ['autodocs'],
} satisfies Meta<typeof NotificationEmpty>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
