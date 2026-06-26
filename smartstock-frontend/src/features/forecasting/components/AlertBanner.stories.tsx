import type { Meta, StoryObj } from '@storybook/react-vite';
import AlertBanner from './AlertBanner';

const mockSku = {
  id: '1',
  sku_code: 'WID-001',
  product_name: 'Widget Alpha',
  current_stock: 5,
  reorder_point: 20,
  predicted_demand_30d: 45,
  stockout_risk: true,
  forecast: [],
  confidence_score: 0.85,
};

const meta = {
  title: 'Forecasting/AlertBanner',
  component: AlertBanner,
  tags: ['autodocs'],
  args: {
    onDismiss: (id: string) => console.log('Dismissed:', id),
  },
} satisfies Meta<typeof AlertBanner>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Critical: Story = {
  args: {
    alert: {
      sku: mockSku,
      severity: 'critical',
      message: 'Widget Alpha stock is at 5 — below reorder point of 20. Consider ordering soon.',
    },
  },
};

export const Warning: Story = {
  args: {
    alert: {
      sku: { ...mockSku, current_stock: 18, stockout_risk: false },
      severity: 'warning',
      message: 'Widget Alpha has only 18 units, which may be insufficient for the forecasted 30-day demand of 45.',
    },
  },
};
