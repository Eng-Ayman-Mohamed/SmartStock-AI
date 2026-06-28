import { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-vite';
import ModeSelector from './ModeSelector';
import type { ChatMode } from '../types';

const meta = {
  title: 'AI Assistant/ModeSelector',
  component: ModeSelector,
  tags: ['autodocs'],
  args: {
    active: 'auto',
    onChange: (mode: ChatMode) => console.log('Mode:', mode),
  },
} satisfies Meta<typeof ModeSelector>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Auto: Story = {
  args: { active: 'auto' },
};

export const NLQuery: Story = {
  args: { active: 'nl_query' },
};

export const RAG: Story = {
  args: { active: 'rag' },
};

export const Interactive: Story = {
  render: (args) => {
    const [active, setActive] = useState<ChatMode>('auto');
    return <ModeSelector {...args} active={active} onChange={setActive} />;
  },
};
