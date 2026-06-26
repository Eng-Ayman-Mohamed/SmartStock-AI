import type { Meta, StoryObj } from '@storybook/react-vite';
import MessageBubble from './MessageBubble';
import type { Message } from '../types';

const meta = {
  title: 'AI Assistant/MessageBubble',
  component: MessageBubble,
  tags: ['autodocs'],
} satisfies Meta<typeof MessageBubble>;

export default meta;
type Story = StoryObj<typeof meta>;

export const UserMessage: Story = {
  args: {
    message: {
      id: '1',
      role: 'user',
      text: 'What products are low on stock?',
      timestamp: Date.now(),
    } satisfies Message,
  },
};

export const AISimple: Story = {
  args: {
    message: {
      id: '2',
      role: 'ai',
      text: 'I found 3 products that are currently low on stock:\n1. Widget Beta (8 units remaining)\n2. Gadget Gamma (0 units)\n3. Component Zeta (3 units)',
      timestamp: Date.now(),
    } satisfies Message,
  },
};

export const AIWithCitation: Story = {
  args: {
    message: {
      id: '3',
      role: 'ai',
      text: 'Based on the supplier agreement [Source: Supplier Contract Q1, Page: 12], the lead time for Widget Beta is 14 days.',
      sources: [
        { document: 'Supplier Contract Q1', page: 12, chunk_text: 'Lead time for standard widgets is 14 business days from order confirmation.' },
      ],
      timestamp: Date.now(),
    } satisfies Message,
  },
};

export const AIMultipleCitations: Story = {
  args: {
    message: {
      id: '4',
      role: 'ai',
      text: 'According to [Source: Inventory Report, Page: 5] and [Source: Supplier Guidelines, Page: 23], the reorder point should be set to 50 units.',
      sources: [
        { document: 'Inventory Report', page: 5, chunk_text: 'Historical data shows optimal reorder point is 50 units for this SKU.' },
        { document: 'Supplier Guidelines', page: 23, chunk_text: 'Minimum order quantity is 50 units for standard products.' },
      ],
      timestamp: Date.now(),
    } satisfies Message,
  },
};

export const AIStreamingPlaceholder: Story = {
  args: {
    message: {
      id: '5',
      role: 'ai',
      text: '',
      timestamp: Date.now(),
    } satisfies Message,
  },
};
