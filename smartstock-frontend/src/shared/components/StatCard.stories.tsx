import type { Meta, StoryObj } from '@storybook/react-vite';
import { Package, DollarSign, Users, AlertTriangle } from 'lucide-react';
import StatCard from './StatCard';

const meta = {
  title: 'Primitives/StatCard',
  component: StatCard,
  tags: ['autodocs'],
  argTypes: {
    accent: {
      control: 'select',
      options: ['orange', 'purple', 'green', 'red', 'none'],
    },
  },
  args: {
    label: 'Total Products',
    value: '1,234',
  },
} satisfies Meta<typeof StatCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithIcon: Story = {
  args: {
    label: 'Total Products',
    value: '1,234',
    icon: Package,
  },
};

export const UpwardTrend: Story = {
  args: {
    label: 'Revenue',
    value: '$48,290',
    icon: DollarSign,
    trend: { direction: 'up', percentage: '12.5%' },
  },
};

export const DownwardTrend: Story = {
  args: {
    label: 'Stockouts',
    value: '23',
    icon: AlertTriangle,
    trend: { direction: 'down', percentage: '8.1%' },
  },
};

export const GreenAccent: Story = {
  args: {
    label: 'Active Users',
    value: '892',
    icon: Users,
    accent: 'green',
    trend: { direction: 'up', percentage: '5.2%' },
  },
};

export const RedAccent: Story = {
  args: {
    label: 'Overdue Orders',
    value: '12',
    accent: 'red',
    trend: { direction: 'up', percentage: '3.1%', color: 'text-red-600' },
  },
};

export const PurpleAccent: Story = {
  args: {
    label: 'AI Predictions',
    value: '96%',
    icon: Package,
    accent: 'purple',
    trend: { direction: 'up', percentage: '2.4%' },
  },
};
