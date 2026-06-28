import type { Meta, StoryObj } from '@storybook/react-vite';
import Card from './Card';
import Button from './Button';

const meta = {
  title: 'Primitives/Card',
  component: Card,
  tags: ['autodocs'],
  argTypes: {
    title: { control: 'text' },
    subtitle: { control: 'text' },
    noPadding: { control: 'boolean' },
  },
  args: {
    children: 'Card content goes here.',
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: 'Card Title',
    children: 'This is a basic card with a title and content.',
  },
};

export const WithSubtitle: Story = {
  args: {
    title: 'Card Title',
    subtitle: 'A brief description of this card section.',
    children: 'Card content with subtitle visible above.',
  },
};

export const WithAction: Story = {
  args: {
    title: 'Inventory Summary',
    action: <Button size="sm" variant="ghost">View All</Button>,
    children: 'Card with an action button in the header.',
  },
};

export const NoTitle: Story = {
  args: {
    children: 'A simple card without a title or header section.',
  },
};

export const NoPadding: Story = {
  args: {
    title: 'Full-bleed Content',
    noPadding: true,
    children: (
      <div className="p-4 sm:p-6">
        Content with no padding on the card body.
      </div>
    ),
  },
};
