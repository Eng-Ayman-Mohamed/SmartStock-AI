import { User, Bell, Shield, Database, RefreshCw } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';

const sections = [
  {
    title: 'Profile',
    icon: User,
    fields: [
      { label: 'Full Name', value: 'John Doe' },
      { label: 'Email', value: 'john.doe@smartstock.ai' },
      { label: 'Role', value: 'Warehouse Manager' },
    ],
  },
  {
    title: 'Notifications',
    icon: Bell,
    fields: [
      { label: 'Low Stock Alerts', value: 'Email + In-app' },
      { label: 'PO Approvals', value: 'Email + In-app' },
      { label: 'Forecast Reports', value: 'Weekly digest' },
    ],
  },
  {
    title: 'Security',
    icon: Shield,
    fields: [
      { label: 'Two-Factor Auth', value: 'Enabled' },
      { label: 'Session Timeout', value: '30 minutes' },
      { label: 'API Access', value: 'Active — 2 keys' },
    ],
  },
];

export default function SettingsPage() {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-page-heading text-gray-900">Settings</h1>
          <p className="text-body text-gray-600 mt-1">Manage your account and application preferences</p>
        </div>
        <Button variant="primary" size="md"><RefreshCw className="w-4 h-4" /> Sync Data</Button>
      </div>

      <div className="max-w-2xl space-y-6">
        {sections.map((section) => (
          <Card key={section.title} title={section.title} action={<Button variant="ghost" size="sm">Edit</Button>}>
            <div className="space-y-4">
              {section.fields.map((field) => (
                <div key={field.label} className="flex items-center justify-between py-1">
                  <span className="text-body text-gray-600">{field.label}</span>
                  <span className="text-body text-gray-900 font-medium">{field.value}</span>
                </div>
              ))}
            </div>
          </Card>
        ))}

        <Card title="Data Management">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-body text-gray-900">Export All Data</p>
                <p className="text-caption text-gray-600">Download inventory, orders, and forecasts as CSV</p>
              </div>
              <Button variant="secondary" size="sm"><Database className="w-4 h-4" /> Export</Button>
            </div>
            <div className="pt-3 border-t-[0.5px] border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-body text-gray-900">Clear Forecast Cache</p>
                  <p className="text-caption text-gray-600">Force re-generation of all demand predictions</p>
                </div>
                <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50">Clear</Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
