import type { Meta, StoryObj } from '@storybook/react-vite';
import ChatEmptyState from './ChatEmptyState';

const meta = {
  title: 'AI Assistant/ChatEmptyState',
  component: ChatEmptyState,
  tags: ['autodocs'],
  args: {
    onSelectSuggestion: (text: string) => console.log('Selected:', text),
  },
} satisfies Meta<typeof ChatEmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
