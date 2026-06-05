import { Package, Plus, Filter } from 'lucide-react';

export default function InventoryPage() {
  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-surface-100">Products & Stock</h2>
          <p className="text-sm text-surface-400 mt-1">Manage your inventory items and stock levels</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 h-9 px-4 rounded-lg bg-surface-800/60 border border-surface-700/50 text-sm text-surface-300 hover:bg-surface-700/60 transition-colors duration-200">
            <Filter className="w-4 h-4" />
            Filters
          </button>
          <button className="flex items-center gap-2 h-9 px-4 rounded-lg bg-gradient-to-r from-brand-600 to-brand-500 text-sm font-medium text-white shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 transition-all duration-200">
            <Plus className="w-4 h-4" />
            Add Product
          </button>
        </div>
      </div>

      {/* Table placeholder */}
      <div className="rounded-2xl border border-surface-800/50 bg-surface-900/60 backdrop-blur-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-surface-800/50">
          <div className="flex items-center gap-2 text-surface-400">
            <Package className="w-4 h-4" />
            <span className="text-sm font-medium">Product Catalog</span>
          </div>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-center h-64 rounded-xl border-2 border-dashed border-surface-800 text-surface-600">
            <p className="text-sm">Product table will be rendered here</p>
          </div>
        </div>
      </div>
    </div>
  );
}
