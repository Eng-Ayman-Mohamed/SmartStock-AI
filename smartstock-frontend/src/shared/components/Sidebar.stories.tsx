import type { Meta, StoryObj } from '@storybook/react-vite';
import Sidebar from './Sidebar';
import { withMockAuth } from '../test-utils/decorators';

const meta = {
  title: 'Layout/Sidebar',
  component: Sidebar,
  tags: ['autodocs'],
  decorators: [withMockAuth],
} satisfies Meta<typeof Sidebar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
