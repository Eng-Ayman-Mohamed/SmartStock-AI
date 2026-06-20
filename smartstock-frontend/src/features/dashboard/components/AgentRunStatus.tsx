import { Activity, CheckCircle, Clock, XCircle, Loader2 } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Skeleton from '../../../shared/components/Skeleton';
import { useAgentRuns } from '../hooks/useAgentRuns';
import type { AgentRun } from '../types';

const statusConfig: Record<AgentRun['status'], { color: string; icon: typeof Clock; label: string }> = {
  running: {
    color: 'bg-brand-50 text-brand-800 border-brand-200 dark:bg-brand-900/30 dark:text-brand-200 dark:border-brand-700',
    icon: Loader2,
    label: 'Running',
  },
  completed: {
    color: 'bg-green-50 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-200 dark:border-green-700',
    icon: CheckCircle,
    label: 'Completed',
  },
  failed: {
    color: 'bg-red-50 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-200 dark:border-red-700',
    icon: XCircle,
    label: 'Failed',
  },
  pending: {
    color: 'bg-orange-50 text-orange-800 border-orange-200 dark:bg-orange-900/30 dark:text-orange-200 dark:border-orange-700',
    icon: Clock,
    label: 'Pending',
  },
};

function AgentRunIndicator({ run }: { run: AgentRun }) {
  const config = statusConfig[run.status];
  const Icon = config.icon;
  const time = run.completed_at || run.started_at || run.created_at;

  return (
    <div className="flex items-center gap-3 pb-3 border-b border-hairline last:border-0 last:pb-0">
      <div className={`flex items-center justify-center w-7 h-7 rounded-md shrink-0 border ${config.color}`}>
        <Icon className={`w-4 h-4 ${run.status === 'running' ? 'animate-spin' : ''}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-body text-ink truncate">{run.agent_name}</p>
        <p className="text-caption text-ink-muted mt-0.5">
          {config.label}
          {time && (
            <span className="ml-1 tabular-nums">
              — {new Date(time).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </p>
      </div>
    </div>
  );
}

export default function AgentRunStatus() {
  const { data: runs, isLoading, error, refetch } = useAgentRuns();

  return (
    <Card title="Agent Run Status" subtitle="Recent AI agent activity">
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton lines={3} />
        </div>
      ) : error ? (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-body text-red-600">Failed to load agent runs.</p>
          <button onClick={() => refetch()} className="underline text-sm font-medium text-red-600">Try again</button>
        </div>
      ) : !runs || runs.length === 0 ? (
        <div className="flex items-center gap-3 py-6">
          <Activity className="w-5 h-5 text-ink-faint" />
          <p className="text-body text-ink-muted">No agent runs recorded yet.</p>
        </div>
      ) : (
        <div className="space-y-0 max-h-[360px] overflow-y-auto overscroll-contain">
          {runs.slice(0, 8).map((run) => (
            <AgentRunIndicator key={run.id} run={run} />
          ))}
        </div>
      )}
    </Card>
  );
}
