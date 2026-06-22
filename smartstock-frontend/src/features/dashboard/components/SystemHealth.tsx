import { Database, Wifi, Cpu, HardDrive, Activity, CheckCircle, XCircle } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Skeleton from '../../../shared/components/Skeleton';
import { useHealthStatus } from '../hooks/useHealthStatus';
import type { HealthStatus } from '../hooks/useHealthStatus';

const subsystems: { key: keyof Omit<HealthStatus, 'status' | 'stale_running_runs'>; label: string; icon: typeof Database }[] = [
  { key: 'database', label: 'Database', icon: Database },
  { key: 'redis', label: 'Redis', icon: Wifi },
  { key: 'celery', label: 'Celery', icon: Cpu },
  { key: 'storage', label: 'Storage', icon: HardDrive },
  { key: 'agents', label: 'Agents', icon: Activity },
];

function StatusDot({ ok }: { ok: boolean }) {
  return ok ? (
    <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
  ) : (
    <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
  );
}

export default function SystemHealth() {
  const { data: health, isLoading, error } = useHealthStatus();

  if (isLoading) {
    return <Skeleton className="h-24" />;
  }

  if (error || !health) {
    return null;
  }

  const overallColor = health.status === 'healthy'
    ? 'border-green-200 dark:border-green-800'
    : health.status === 'degraded'
      ? 'border-orange-200 dark:border-orange-800'
      : 'border-red-200 dark:border-red-800';

  return (
    <Card title="System Health" subtitle={`Status: ${health.status}`}>
      <div className={`border rounded-lg p-3 ${overallColor}`}>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {subsystems.map(({ key, label, icon: Icon }) => (
            <div key={key} className="flex items-center gap-2">
              <Icon className="w-4 h-4 text-ink-faint" />
              <span className="text-caption text-ink-muted">{label}</span>
              <StatusDot ok={health[key] === 'ok'} />
            </div>
          ))}
        </div>
        {health.stale_running_runs > 0 && (
          <p className="text-caption text-orange-600 dark:text-orange-400 mt-2">
            {health.stale_running_runs} stale running agent run{health.stale_running_runs !== 1 ? 's' : ''}
          </p>
        )}
      </div>
    </Card>
  );
}
