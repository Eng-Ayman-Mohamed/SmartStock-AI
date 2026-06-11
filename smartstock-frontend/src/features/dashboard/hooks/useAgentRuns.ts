import { useQuery } from '@tanstack/react-query';
import { fetchAgentRuns } from '../api';
import type { AgentRun } from '../types';

export function useAgentRuns() {
  return useQuery<AgentRun[]>({
    queryKey: ['agent-runs'],
    queryFn: fetchAgentRuns,
    refetchInterval: 15_000,
  });
}
