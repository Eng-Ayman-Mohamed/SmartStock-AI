import { Package, AlertTriangle, FileText, TrendingUp } from 'lucide-react';
import Card from '../../../shared/components/Card';
import ChatPanel from '../components/ChatPanel';

export default function AIAssistantPage() {
  return (
    <div className="h-[calc(100vh-40px-64px)] animate-fadeIn flex flex-col">
      <div className="flex items-center justify-between mb-6">
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
              {[
                { name: 'Wireless Mouse', stock: 12, threshold: 50, icon: Package },
                { name: 'USB-C Hub 6-in-1', stock: 28, threshold: 60, icon: Package },
                { name: 'Mechanical Keyboard', stock: 15, threshold: 30, icon: Package },
                { name: '27" Monitor Stand', stock: 8, threshold: 20, icon: Package },
                { name: 'Webcam HD', stock: 42, threshold: 35, icon: Package },
              ].map((item) => (
                <div key={item.name} className="flex items-center gap-3 pb-2 border-b border-hairline last:border-0 last:pb-0">
                  <div className={`flex items-center justify-center w-7 h-7 rounded-md shrink-0 ${
                    item.stock < item.threshold ? 'bg-orange-50' : 'bg-green-50'
                  }`}>
                    <item.icon className={`w-4 h-4 ${item.stock < item.threshold ? 'text-orange-600' : 'text-green-600'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-body text-ink truncate">{item.name}</p>
                    <p className="text-caption text-ink-muted tabular-nums">{item.stock} units</p>
                  </div>
                  {item.stock < item.threshold && <AlertTriangle className="w-4 h-4 text-orange-600" />}
                </div>
              ))}
            </div>
          </Card>

          <Card title="Data Sources">
            <div className="space-y-2">
              {[
                { name: 'Inventory DB', status: 'Connected', icon: Package },
                { name: 'Sales Pipeline', status: 'Connected', icon: TrendingUp },
                { name: 'Supplier Catalog', status: 'Synced 2h ago', icon: FileText },
              ].map((src) => (
                <div key={src.name} className="flex items-center gap-2 text-body text-ink-muted">
                  <src.icon className="w-4 h-4 text-ink-faint" />
                  <span className="flex-1">{src.name}</span>
                  <span className="text-caption text-green-600">{src.status}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
