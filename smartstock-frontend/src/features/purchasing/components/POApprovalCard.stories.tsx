import type { Meta, StoryObj } from '@storybook/react-vite';
import POApprovalCard from './POApprovalCard';
import { withQueryClient } from '../../../shared/test-utils/decorators';
import type { PendingPO } from '../types';

const mockPO: PendingPO = {
  id: 'PO-2024-0421',
  product: 'Widget Alpha',
  sku: 'WID-001',
  supplier: 'Acme Supplies Inc.',
  predicted_stockout: 'Jul 15, 2026',
  recommended_qty: 150,
  unit_cost: 12.50,
  estimated_total_cost: '$1,875.00',
  agent_reasoning: 'Widget Alpha has been trending at 45 units/week for the last 4 weeks. With current stock at 8 units and a 14-day lead time, ordering 150 units ensures 3 weeks of safety stock above the forecasted demand.',
};

const meta = {
  title: 'Purchasing/POApprovalCard',
  component: POApprovalCard,
  tags: ['autodocs'],
  decorators: [withQueryClient],
  args: {
    po: mockPO,
  },
} satisfies Meta<typeof POApprovalCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const ReadOnly: Story = {
  args: { readOnly: true },
};

export const WithLongReasoning: Story = {
  args: {
    po: {
      ...mockPO,
      agent_reasoning: 'Detailed analysis:\n1. Current stock: 8 units (below reorder point of 20)\n2. Weekly consumption: 45 units\n3. Lead time: 14 days\n4. Safety stock recommended: 3 weeks\n5. Recommendation: Order 150 units to cover 3 weeks of demand plus safety buffer.\n\nThis recommendation is based on the supplier agreement [Source: Supplier Contract Q1, Page: 12] and historical consumption data from the last 90 days.',
    },
  },
};
