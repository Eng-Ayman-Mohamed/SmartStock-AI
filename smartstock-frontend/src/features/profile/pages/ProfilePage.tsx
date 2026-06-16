import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import Skeleton from '../../../shared/components/Skeleton';
import RoleBadge from '../../users/components/RoleBadge';
import { useAuthStore } from '../../../store/authStore';

const sectionFields: Record<string, { label: string; value: string }[]> = {
  Notifications: [
    { label: 'Low Stock Alerts', value: 'Email + In-app' },
    { label: 'PO Approvals', value: 'Email + In-app' },
    { label: 'Forecast Reports', value: 'Weekly digest' },
  ],
  Security: [
    { label: 'Session Timeout', value: '30 minutes' },
    { label: 'API Access', value: 'Active — 2 keys' },
  ],
};

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const isBootstrapping = useAuthStore((s) => s.isBootstrapping);

  if (isBootstrapping) {
    return (
      <div className="space-y-6 animate-fadeIn">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-page-heading text-ink">Profile</h1>
        <p className="text-body text-ink-muted mt-1">Your account information and preferences</p>
      </div>

      <div className="max-w-2xl space-y-6">
        <Card title="Account" action={<Button variant="ghost" size="sm">Edit</Button>}>
          <div className="space-y-4">
            <div className="flex items-center gap-3 pb-4 border-b-[0.5px] border-hairline">
              <div
                className="w-12 h-12 rounded-full bg-brand-600 flex items-center justify-center text-white text-card-title font-medium"
                aria-hidden="true"
              >
                {(user?.name ?? '?')
                  .split(' ')
                  .map((n) => n[0])
                  .join('')
                  .toUpperCase()
                  .slice(0, 2)}
              </div>
              <div className="min-w-0">
                <p className="text-body text-ink font-medium">{user?.name ?? '—'}</p>
                <p className="text-caption text-ink-muted">{user?.email ?? '—'}</p>
              </div>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-body text-ink-muted">Role</span>
              {user && <RoleBadge role={user.role} />}
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-body text-ink-muted">User ID</span>
              <span className="text-body text-ink font-medium">{user?.id ?? '—'}</span>
            </div>
          </div>
        </Card>

        {Object.entries(sectionFields).map(([title, fields]) => (
          <Card
            key={title}
            title={title}
            action={
              <Button variant="ghost" size="sm">
                Edit
              </Button>
            }
          >
            <div className="space-y-4">
              {fields.map((field) => (
                <div key={field.label} className="flex items-center justify-between py-1">
                  <span className="text-body text-ink-muted">{field.label}</span>
                  <span className="text-body text-ink font-medium">{field.value}</span>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
