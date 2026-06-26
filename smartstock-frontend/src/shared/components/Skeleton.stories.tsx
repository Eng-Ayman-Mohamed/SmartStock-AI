import type { Meta, StoryObj } from '@storybook/react-vite';
import Skeleton from './Skeleton';
import Card from './Card';

const meta = {
  title: 'Primitives/Skeleton',
  component: Skeleton,
  tags: ['autodocs'],
  argTypes: {
    className: { control: 'text' },
    lines: { control: { type: 'number', min: 1, max: 10 } },
  },
} satisfies Meta<typeof Skeleton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Block: Story = {
  args: {
    className: 'w-full h-32',
  },
};

export const SmallBlock: Story = {
  args: {
    className: 'w-24 h-6',
  },
};

export const TextLines: Story = {
  args: {
    lines: 3,
  },
};

export const FiveLines: Story = {
  args: {
    lines: 5,
  },
};

export const CardSkeleton: Story = {
  render: () => (
    <Card title="Loading...">
      <Skeleton lines={4} />
    </Card>
  ),
};
