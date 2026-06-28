import type { Meta, StoryObj } from '@storybook/react-vite';
import RoleBadge from './RoleBadge';

const meta = {
  title: 'Users/RoleBadge',
  component: RoleBadge,
  tags: ['autodocs'],
  argTypes: {
    role: {
      control: 'select',
      options: ['viewer', 'manager', 'admin'],
    },
  },
} satisfies Meta<typeof RoleBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Viewer: Story = {
  args: { role: 'viewer' },
};

export const Manager: Story = {
  args: { role: 'manager' },
};

export const Admin: Story = {
  args: { role: 'admin' },
};
