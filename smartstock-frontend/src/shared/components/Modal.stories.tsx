import { useState } from 'react';
import type { Meta, StoryObj } from '@storybook/react-vite';
import Modal from './Modal';
import Button from './Button';

const meta = {
  title: 'Primitives/Modal',
  component: Modal,
  tags: ['autodocs'],
  argTypes: {
    open: { control: 'boolean' },
    title: { control: 'text' },
  },
  args: {
    open: true,
    title: 'Modal Title',
    children: 'This is the modal content area.',
    onClose: () => {},
  },
} satisfies Meta<typeof Modal>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const WithFooter: Story = {
  args: {
    footer: (
      <div className="flex gap-2">
        <Button variant="secondary" size="sm">Cancel</Button>
        <Button variant="primary" size="sm">Confirm</Button>
      </div>
    ),
  },
};

export const LongContent: Story = {
  args: {
    title: 'Terms & Conditions',
    children: (
      <div className="space-y-4">
        {Array.from({ length: 15 }).map((_, i) => (
          <p key={i}>
            Section {i + 1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
          </p>
        ))}
      </div>
    ),
    footer: (
      <Button variant="primary" size="sm">Accept</Button>
    ),
  },
};

export const NoTitle: Story = {
  args: {
    title: undefined,
    children: 'A modal without a title or header.',
  },
};

export const Interactive: Story = {
  render: (args) => {
    const [open, setOpen] = useState(false);
    return (
      <div>
        <Button onClick={() => setOpen(true)}>Open Modal</Button>
        <Modal {...args} open={open} onClose={() => setOpen(false)} />
      </div>
    );
  },
  args: {
    title: 'Interactive Modal',
    children: 'Click outside or press Escape to close.',
    footer: (
      <Button variant="primary" size="sm" onClick={() => {}}>Save</Button>
    ),
  },
};
