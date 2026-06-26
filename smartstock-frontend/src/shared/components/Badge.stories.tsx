import type { Meta, StoryObj } from '@storybook/react-vite';
import Badge from './Badge';

const meta = {
  title: 'Primitives/Badge',
  component: Badge,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: [
        'In Stock', 'Low Stock', 'Out of Stock', 'Draft',
        'Pending Approval', 'Approved', 'Sent', 'Confirmed',
        'Rejected', 'AI Generated', 'Viewer', 'Manager', 'Admin',
        'Active', 'Inactive',
      ],
    },
    showDot: { control: 'boolean' },
    children: { control: 'text' },
  },
  args: {
    showDot: true,
  },
} satisfies Meta<typeof Badge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const InStock: Story = {
  args: { variant: 'In Stock', children: 'In Stock' },
};

export const LowStock: Story = {
  args: { variant: 'Low Stock', children: 'Low Stock' },
};

export const OutOfStock: Story = {
  args: { variant: 'Out of Stock', children: 'Out of Stock' },
};

export const Draft: Story = {
  args: { variant: 'Draft', children: 'Draft', showDot: false },
};

export const PendingApproval: Story = {
  args: { variant: 'Pending Approval', children: 'Pending Approval' },
};

export const Approved: Story = {
  args: { variant: 'Approved', children: 'Approved' },
};

export const Rejected: Story = {
  args: { variant: 'Rejected', children: 'Rejected' },
};

export const AIGenerated: Story = {
  args: { variant: 'AI Generated', children: 'AI Generated' },
};

export const Admin: Story = {
  args: { variant: 'Admin', children: 'Admin' },
};

export const Manager: Story = {
  args: { variant: 'Manager', children: 'Manager' },
};

export const Viewer: Story = {
  args: { variant: 'Viewer', children: 'Viewer' },
};

export const Active: Story = {
  args: { variant: 'Active', children: 'Active' },
};

export const Inactive: Story = {
  args: { variant: 'Inactive', children: 'Inactive', showDot: false },
};

export const WithoutDot: Story = {
  args: { variant: 'In Stock', children: 'In Stock', showDot: false },
};
