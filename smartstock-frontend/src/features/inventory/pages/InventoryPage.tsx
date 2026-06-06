import { useState } from 'react';
import { Package, Plus, Download, Search } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import DataTable from '../../../shared/components/DataTable';
import EmptyState from '../../../shared/components/EmptyState';
import Badge from '../../../shared/components/Badge';
import type { Column } from '../../../shared/components/DataTable';

interface Product {
  sku: string;
  name: string;
  category: string;
  onHand: number;
  reserved: number;
  reorderPoint: number;
  supplier: string;
  status: string;
}

const products: Product[] = [];

const columns: Column<Product>[] = [
  { key: 'sku', label: 'SKU', width: '130px', render: (r) => <span className="text-mono text-gray-600">{r.sku}</span> },
  { key: 'name', label: 'Product Name', render: (r) => <span className="truncate block">{r.name}</span> },
  { key: 'category', label: 'Category', width: '120px', render: (r) => <span className="text-gray-600">{r.category}</span> },
  { key: 'onHand', label: 'On Hand', align: 'right', width: '90px', render: (r) => <span className="tabular-nums">{r.onHand}</span> },
  { key: 'reserved', label: 'Reserved', align: 'right', width: '90px', render: (r) => <span className="tabular-nums">{r.reserved}</span> },
  { key: 'reorder', label: 'Reorder Pt', align: 'right', width: '90px', render: (r) => <span className="tabular-nums">{r.reorderPoint}</span> },
  { key: 'supplier', label: 'Supplier', width: '140px', render: (r) => <span className="truncate block text-gray-600">{r.supplier}</span> },
  { key: 'status', label: 'Status', width: '120px', render: (r) => <Badge>{r.status}</Badge> },
];

export default function InventoryPage() {
  const [search, setSearch] = useState('');

  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.sku.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-page-heading text-gray-900">Inventory</h1>
          <p className="text-body text-gray-600 mt-1">Manage your inventory items and stock levels</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="md"><Download className="w-4 h-4" /> Export CSV</Button>
          <Button variant="primary" size="md"><Plus className="w-4 h-4" /> Add Product</Button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
          <input
            type="text"
            placeholder="Search by product name or SKU..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-9 pl-10 pr-4 rounded-md border-[0.5px] border-gray-100 bg-white text-body text-gray-900 placeholder:text-gray-400 hover:border-gray-400 focus:border-brand-600 focus:outline-none focus:ring-0 transition-colors duration-150"
            aria-label="Search products"
          />
        </div>
        <select className="h-9 px-3 rounded-md border-[0.5px] border-gray-100 bg-white text-body text-gray-600 hover:border-gray-400 focus:border-brand-600 focus:outline-none transition-colors duration-150" aria-label="Category filter">
          <option>All categories</option>
        </select>
        <select className="h-9 px-3 rounded-md border-[0.5px] border-gray-100 bg-white text-body text-gray-600 hover:border-gray-400 focus:border-brand-600 focus:outline-none transition-colors duration-150" aria-label="Status filter">
          <option>All statuses</option>
        </select>
      </div>

      <Card>
        <DataTable
          columns={columns}
          data={filtered}
          keyExtractor={(r) => r.sku}
          caption="Product inventory list"
          emptyState={
            <EmptyState
              icon={Package}
              heading="No products yet"
              body="Add your first product to start tracking inventory."
              actionLabel="Add Product"
              onAction={() => {}}
            />
          }
        />
        {filtered.length > 0 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t-[0.5px] border-gray-100">
            <span className="text-caption text-gray-600 tabular-nums">Showing 1–{filtered.length} of {filtered.length} results</span>
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm" disabled>Previous</Button>
              <Button variant="secondary" size="sm" disabled>Next</Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
