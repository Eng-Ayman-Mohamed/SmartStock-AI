import type { Meta, StoryObj } from '@storybook/react-vite';
import PasswordField from './PasswordField';

const meta = {
  title: 'Primitives/PasswordField',
  component: PasswordField,
  tags: ['autodocs'],
  argTypes: {
    placeholder: { control: 'text' },
    disabled: { control: 'boolean' },
    error: { control: 'boolean' },
    value: { control: 'text' },
  },
  args: {
    placeholder: 'Enter password',
    value: '',
  },
} satisfies Meta<typeof PasswordField>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithValue: Story = {
  args: {
    value: 'my-secret-password',
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    value: 'password',
  },
};

export const Error: Story = {
  args: {
    error: true,
    value: 'wrong',
  },
};

export const WithCustomPlaceholder: Story = {
  args: {
    placeholder: 'Current password',
  },
};
