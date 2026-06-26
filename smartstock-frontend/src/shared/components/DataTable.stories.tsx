import { useState, useCallback } from 'react';
import type { Meta, StoryObj } from '@storybook/react-vite';
import DataTable from './DataTable';
import Badge from './Badge';
import Skeleton from './Skeleton';
import EmptyState from './EmptyState';
import { PackageSearch } from 'lucide-react';

interface Product {
  id: string;
  name: string;
  sku: string;
  stock: number;
  status: string;
}

const sampleData: Product[] = [
  { id: '1', name: 'Widget Alpha', sku: 'WID-001', stock: 142, status: 'In Stock' },
  { id: '2', name: 'Widget Beta', sku: 'WID-002', stock: 8, status: 'Low Stock' },
  { id: '3', name: 'Gadget Gamma', sku: 'GAD-001', stock: 0, status: 'Out of Stock' },
  { id: '4', name: 'Gadget Delta', sku: 'GAD-002', stock: 56, status: 'In Stock' },
  { id: '5', name: 'Component Epsilon', sku: 'CMP-001', stock: 234, status: 'In Stock' },
  { id: '6', name: 'Component Zeta', sku: 'CMP-002', stock: 3, status: 'Low Stock' },
  { id: '7', name: 'Tool Eta', sku: 'TOL-001', stock: 19, status: 'In Stock' },
  { id: '8', name: 'Tool Theta', sku: 'TOL-002', stock: 0, status: 'Out of Stock' },
];

const columns = [
  { key: 'name', label: 'Product Name', width: '30%', render: (row: Product) => row.name, sortable: true },
  { key: 'sku', label: 'SKU', width: '20%', render: (row: Product) => row.sku, sortable: true },
  { key: 'stock', label: 'Stock', width: '15%', render: (row: Product) => row.stock.toLocaleString(), sortable: true },
  {
    key: 'status',
    label: 'Status',
    width: '20%',
    render: (row: Product) => <Badge variant={row.status}>{row.status}</Badge>,
    sortable: true,
  },
];

const emptyState = (
  <EmptyState
    icon={PackageSearch}
    heading="No products found"
    body="Try adjusting your search or filter criteria."
  />
);

const meta = {
  title: 'Primitives/DataTable',
  component: DataTable<Product>,
  tags: ['autodocs'],
  args: {
    columns,
    keyExtractor: (row: Product) => row.id,
    caption: 'Products table',
  },
} satisfies Meta<typeof DataTable<Product>>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    data: sampleData,
  },
};

export const Empty: Story = {
  args: {
    data: [],
    emptyState,
  },
};

export const Loading: Story = {
  args: {
    data: [],
    emptyState: (
      <div className="p-4">
        <Skeleton lines={6} />
      </div>
    ),
  },
};

export const WithPagination: Story = {
  args: {
    data: sampleData,
    pagination: {
      currentPage: 1,
      totalPages: 3,
      total: 24,
      startItem: 1,
      endItem: 8,
      hasPrev: false,
      hasNext: true,
      pages: [1, 2, 3],
      onPageChange: (page) => console.log('Page:', page),
      itemLabel: 'products',
    },
  },
};

export const Sortable: Story = {
  render: (args) => {
    const [sortKey, setSortKey] = useState<string | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
    const handleSort = useCallback((key: string) => {
      setSortKey((prev) => {
        if (prev === key) {
          setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
          return key;
        }
        setSortOrder('asc');
        return key;
      });
    }, []);
    const sortedColumns = columns.map((col) => ({
      ...col,
      sortOrder: col.key === sortKey ? sortOrder : undefined,
      sortable: true,
    }));
    const sorted = [...sampleData].sort((a, b) => {
      const aVal = a[sortKey as keyof Product]?.toString() ?? '';
      const bVal = b[sortKey as keyof Product]?.toString() ?? '';
      return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    return (
      <DataTable
        {...args}
        columns={sortedColumns}
        data={sorted}
        onSort={handleSort}
      />
    );
  },
};
