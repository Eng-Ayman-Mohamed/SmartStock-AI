import type { Meta, StoryObj } from '@storybook/react-vite';
import NotificationItem from './NotificationItem';
import { useAuthStore } from '../../../store/authStore';

const mockNotification = {
  id: 1,
  type: 'monitoring' as const,
  severity: 'info' as const,
  title: 'System health check passed',
  message: 'All systems are operating within normal parameters.',
  metadata: {},
  is_read: false,
  created_at: '2026-06-26T10:30:00Z',
  updated_at: '2026-06-26T10:30:00Z',
};

const meta = {
  title: 'Notifications/NotificationItem',
  component: NotificationItem,
  tags: ['autodocs'],
  decorators: [
    (Story) => {
      useAuthStore.setState({
        user: { id: 1, email: 'admin@smartstock.ai', name: 'Admin', role: 'admin', is_active: true },
        token: 'mock-token',
        isBootstrapping: false,
      });
      return <Story />;
    },
  ],
  args: {
    onClose: () => {},
  },
} satisfies Meta<typeof NotificationItem>;

export default meta;
type Story = StoryObj<typeof meta>;

export const InfoUnread: Story = {
  args: {
    notification: {
      ...mockNotification,
      severity: 'info',
      title: 'Forecast updated',
      message: 'Demand forecast for Q3 has been updated with new data.',
    },
  },
};

export const WarningUnread: Story = {
  args: {
    notification: {
      ...mockNotification,
      severity: 'warning',
      title: 'Low stock alert',
      message: 'Widget Alpha is running low. Current stock: 8 units.',
      is_read: false,
    },
  },
};

export const CriticalUnread: Story = {
  args: {
    notification: {
      ...mockNotification,
      severity: 'critical',
      title: 'Stockout detected',
      message: 'Gadget Gamma is out of stock. Reorder immediately.',
      is_read: false,
    },
  },
};

export const Read: Story = {
  args: {
    notification: {
      ...mockNotification,
      severity: 'info',
      title: 'Report generated',
      message: 'Monthly inventory report has been generated successfully.',
      is_read: true,
    },
  },
};

export const Escalation: Story = {
  args: {
    notification: {
      ...mockNotification,
      type: 'escalation',
      severity: 'critical',
      title: 'Approval required',
      message: 'Purchase order #PO-2024-0421 requires your approval.',
      is_read: false,
    },
  },
};
