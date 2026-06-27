import { useQuery } from '@tanstack/react-query';
import { fetchAgentRuns } from '../api';
import { useAuthStore } from '../../../store/authStore';
import type { AgentRun } from '../types';

export function useAgentRuns() {
  const token = useAuthStore((s) => s.token);
  return useQuery<AgentRun[]>({
    queryKey: ['agent-runs'],
    queryFn: fetchAgentRuns,
    refetchInterval: 60_000,
    enabled: !!token,
    retry: false,
  });
}
