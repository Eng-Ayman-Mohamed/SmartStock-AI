import type { Meta, StoryObj } from '@storybook/react-vite';
import ThemeToggle from './ThemeToggle';

const meta = {
  title: 'Layout/ThemeToggle',
  component: ThemeToggle,
  tags: ['autodocs'],
  parameters: {
    backgrounds: { disable: true },
  },
} satisfies Meta<typeof ThemeToggle>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
