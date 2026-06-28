import type { Meta, StoryObj } from '@storybook/react-vite';
import { PackageSearch, Files, SearchX } from 'lucide-react';
import EmptyState from './EmptyState';

const meta = {
  title: 'Primitives/EmptyState',
  component: EmptyState,
  tags: ['autodocs'],
  argTypes: {
    heading: { control: 'text' },
    body: { control: 'text' },
    actionLabel: { control: 'text' },
  },
  args: {
    icon: PackageSearch,
    heading: 'No items found',
    body: 'There are no items to display. Add one to get started.',
  },
} satisfies Meta<typeof EmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithAction: Story = {
  args: {
    actionLabel: 'Add Item',
    onAction: () => alert('Action clicked'),
  },
};

export const SearchEmpty: Story = {
  args: {
    icon: SearchX,
    heading: 'No results',
    body: 'Try adjusting your search or filter criteria.',
  },
};

export const NoDocuments: Story = {
  args: {
    icon: Files,
    heading: 'No documents yet',
    body: 'Upload your first document to get started with AI-powered analysis.',
    actionLabel: 'Upload Document',
    onAction: () => alert('Upload clicked'),
  },
};
