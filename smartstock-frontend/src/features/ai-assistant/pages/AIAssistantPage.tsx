import { Package, AlertTriangle } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Skeleton from '../../../shared/components/Skeleton';
import ChatPanel from '../components/ChatPanel';
import { useInventorySnapshot } from '../hooks/useInventorySnapshot';

export default function AIAssistantPage() {
  const { data: snapshot, isLoading: snapshotLoading } = useInventorySnapshot();
  const items = snapshot ?? [];

  return (
    <div className="h-[calc(100vh-40px-64px)] animate-fadeIn flex flex-col">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-page-heading text-ink">AI Assistant</h1>
          <p className="text-body text-ink-muted mt-1">Your warehouse brain — ask about stock, forecasts, or suppliers</p>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-6 min-h-0">
        <Card noPadding className="flex flex-col overflow-hidden">
          <ChatPanel />
        </Card>

        <div className="space-y-4 overflow-y-auto">
          <Card title="Current Inventory Snapshot">
            <div className="space-y-3">
              {snapshotLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-9" />)}
                </div>
              ) : items.length === 0 ? (
                <p className="text-caption text-ink-muted">No inventory data available.</p>
              ) : (
                items.map((item) => (
                  <div key={item.sku_code} className="flex items-center gap-3 pb-2 border-b border-hairline last:border-0 last:pb-0">
                    <div className={`flex items-center justify-center w-7 h-7 rounded-md shrink-0 ${
                      item.quantity < item.reorder_point ? 'bg-orange-50' : 'bg-green-50'
                    }`}>
                      <Package className={`w-4 h-4 ${item.quantity < item.reorder_point ? 'text-orange-600' : 'text-green-600'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-body text-ink truncate">{item.product_name}</p>
                      <p className="text-caption text-ink-muted tabular-nums">{item.quantity} units</p>
                    </div>
                    {item.quantity < item.reorder_point && <AlertTriangle className="w-4 h-4 text-orange-600" />}
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
