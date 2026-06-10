import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import StatCard from '../../../shared/components/StatCard';
import Card from '../../../shared/components/Card';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import DataTable from '../../../shared/components/DataTable';
import type { Column } from '../../../shared/components/DataTable';
import { Package, AlertTriangle, ShoppingCart, TrendingUp, Download } from 'lucide-react';

const chartData = [
  { date: '01 Jun', demand: 120, actual: 115, upper: 140, lower: 100 },
  { date: '05 Jun', demand: 145, actual: 138, upper: 170, lower: 120 },
  { date: '10 Jun', demand: 130, actual: null, upper: 160, lower: 105 },
  { date: '15 Jun', demand: 160, actual: null, upper: 190, lower: 130 },
  { date: '20 Jun', demand: 150, actual: null, upper: 180, lower: 120 },
  { date: '25 Jun', demand: 175, actual: null, upper: 205, lower: 145 },
  { date: '30 Jun', demand: 165, actual: null, upper: 195, lower: 135 },
];

function ForecastChart() {
  return (
    <div className="h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
           <CartesianGrid strokeDasharray="3 3" stroke="var(--color-hairline)" horizontal={true} vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12, fill: 'var(--color-ink-faint)' }}
            tickLine={false}
            axisLine={{ stroke: 'var(--color-hairline)', strokeWidth: 0.5 }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: 'var(--color-ink-faint)' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--color-canvas)',
              border: '1px solid var(--color-hairline)',
              borderRadius: '8px',
              boxShadow: 'var(--shadow-soft)',
              fontSize: '14px',
            }}
            labelStyle={{ fontSize: '12px', color: 'var(--color-ink-faint)' }}
          />
          <Area
            type="monotone"
            dataKey="upper"
            stroke="var(--color-brand-100)"
            strokeWidth={1}
            strokeDasharray="4 4"
            fill="var(--color-brand-50)"
            fillOpacity={0.4}
            dot={false}
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="var(--color-brand-100)"
            strokeWidth={1}
            strokeDasharray="4 4"
            fill="none"
            dot={false}
          />
          <Area
            type="monotone"
            dataKey="demand"
            stroke="var(--color-brand-600)"
            strokeWidth={2}
            fill="none"
            dot={false}
            activeDot={{ r: 4, fill: 'var(--color-brand-600)' }}
          />
          <Area
            type="monotone"
            dataKey="actual"
            stroke="var(--color-ink-secondary)"
            strokeWidth={1.5}
            strokeDasharray="6 4"
            fill="none"
            dot={false}
            connectNulls={false}
          />
          <ReferenceLine
            y={150}
            stroke="var(--color-orange-600)"
            strokeWidth={1.5}
            strokeDasharray="6 4"
            label={{
              value: 'Reorder point',
              position: 'insideTopRight',
              fontSize: 11,
              fill: 'var(--color-orange-600)',
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-4 mt-2 text-caption text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-brand-600" /> Predicted demand
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-0.5" style={{ borderTop: '1.5px dashed var(--color-ink-secondary)', height: 0 }} /> Actual sales
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-[9px] bg-brand-50 border-[0.5px] border-brand-100" /> Confidence interval
        </span>
      </div>
    </div>
  );
}

const alertItems = [
  { product: 'Wireless Mouse', sku: 'WM-2024-001', stock: 12, reorder: 50, severity: 'critical' as const },
  { product: 'USB-C Hub 6-in-1', sku: 'UC-2024-042', stock: 28, reorder: 60, severity: 'critical' as const },
  { product: 'Mechanical Keyboard', sku: 'MK-2024-017', stock: 15, reorder: 30, severity: 'warning' as const },
  { product: '27" Monitor Stand', sku: 'MS-2024-088', stock: 8, reorder: 20, severity: 'warning' as const },
];

interface PurchaseOrder {
  id: string;
  product: string;
  supplier: string;
  qty: number;
  cost: string;
  status: string;
  date: string;
}

const poData: PurchaseOrder[] = [
  { id: 'PO-1042', product: 'Wireless Mouse', supplier: 'TechSupply Co.', qty: 200, cost: '$4,250.00', status: 'Pending Approval', date: '02 Jun 2025' },
  { id: 'PO-1043', product: 'USB-C Hub', supplier: 'Warehouse Direct', qty: 100, cost: '$1,800.00', status: 'Approved', date: '01 Jun 2025' },
  { id: 'PO-1044', product: 'Mechanical Keyboard', supplier: 'Global Parts Inc.', qty: 75, cost: '$3,200.00', status: 'Pending Approval', date: '31 May 2025' },
  { id: 'PO-1045', product: 'Monitor Stand', supplier: 'Local Distributors', qty: 50, cost: '$950.00', status: 'Approved', date: '30 May 2025' },
  { id: 'PO-1046', product: 'Webcam HD', supplier: 'TechSupply Co.', qty: 150, cost: '$2,800.00', status: 'Sent', date: '28 May 2025' },
];

const poColumns: Column<PurchaseOrder>[] = [
  { key: 'po', label: 'PO Number', width: '110px', render: (r) => <span className="text-mono text-ink-muted">{r.id}</span> },
  { key: 'product', label: 'Product', render: (r) => <span className="truncate block">{r.product}</span> },
  { key: 'supplier', label: 'Supplier', render: (r) => <span className="truncate block text-ink-muted">{r.supplier}</span> },
  { key: 'qty', label: 'Qty', align: 'right', width: '70px', render: (r) => <span className="tabular-nums">{r.qty}</span> },
  { key: 'cost', label: 'Cost', align: 'right', width: '110px', render: (r) => <span className="tabular-nums">{r.cost}</span> },
  { key: 'status', label: 'Status', width: '140px', render: (r) => <Badge>{r.status}</Badge> },
  { key: 'date', label: 'Date', width: '110px', render: (r) => <span className="text-caption text-ink-muted tabular-nums">{r.date}</span> },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-page-heading text-ink">Dashboard</h1>
        <p className="text-body text-ink-muted mt-1">Good morning, John. You have 3 pending POs.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard label="Total SKUs" value="1,247" icon={Package} />
        <StatCard label="Low Stock Alerts" value="23" accent="orange" icon={AlertTriangle} trend={{ direction: 'up', percentage: '12%', color: 'text-orange-600' }} />
        <StatCard label="Pending POs" value="8" accent="orange" icon={ShoppingCart} />
        <StatCard label="Forecast Accuracy" value="87.4%" accent="purple" icon={TrendingUp} trend={{ direction: 'up', percentage: '2.1%' }} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
        <Card title="30-Day Demand Forecast">
          <ForecastChart />
        </Card>

        <Card title="Reorder Alerts" action={<Button variant="ghost" size="sm">View all</Button>}>
          <div className="space-y-3">
            {alertItems.map((item) => (
              <div key={item.sku} className="flex items-start gap-3 pb-3 border-b border-hairline last:border-0 last:pb-0">
                <div className={`flex items-center justify-center w-7 h-7 rounded-md shrink-0 ${
                  item.severity === 'critical' ? 'bg-red-50' : 'bg-orange-50'
                }`}>
                  <AlertTriangle className={`w-4 h-4 ${
                    item.severity === 'critical' ? 'text-red-600' : 'text-orange-600'
                  }`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-body text-ink truncate">{item.product}</p>
                  <p className="text-caption text-ink-muted tabular-nums mt-0.5">{item.stock} units — reorder at {item.reorder}</p>
                </div>
                <Badge variant={item.severity === 'critical' ? 'Out of Stock' : 'Low Stock'}>
                  {item.severity === 'critical' ? 'Critical' : 'Low'}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card
        title="Recent Purchase Orders"
        action={
          <div className="flex items-center gap-2">
            <Button variant="utility" size="sm"><Download className="w-4 h-4" /> Export CSV</Button>
          </div>
        }
      >
        <DataTable
          columns={poColumns}
          data={poData}
          keyExtractor={(r) => r.id}
          caption="Recent purchase orders"
        />
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-hairline">
          <span className="text-caption text-ink-muted tabular-nums">Showing 1–5 of 5 results</span>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" disabled>Previous</Button>
            <Button variant="secondary" size="sm" disabled>Next</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
