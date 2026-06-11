import api from '../../lib/axios';
import type { AgentRun, OverdueSupplier, PurchaseOrder, ReorderAlert } from './types';

export async function fetchLowStockItems(): Promise<ReorderAlert[]> {
  const { data } = await api.get<{ status: string; data: ReorderAlert[] }>(
    '/inventory/stock-levels/low_stock/'
  );
  return data.data;
}

export async function fetchAgentRuns(): Promise<AgentRun[]> {
  const { data } = await api.get<{ status: string; data: AgentRun[] }>(
    '/audit/logs/agent-runs/',
    { params: { page_size: 100 } }
  );
  return data.data;
}

export async function fetchPendingPOs(): Promise<PurchaseOrder[]> {
  const { data } = await api.get<{ status: string; data: PurchaseOrder[] }>(
    '/purchasing/orders/',
    { params: { status: 'pending_approval', page_size: 100 } }
  );
  return data.data;
}

export async function approvePO(poId: number): Promise<void> {
  await api.post(`/purchasing/orders/${poId}/approve/`);
}

export async function rejectPO(poId: number): Promise<void> {
  await api.post(`/purchasing/orders/${poId}/reject/`);
}

export async function fetchOverdueSuppliers(): Promise<OverdueSupplier[]> {
  const { data } = await api.get<{ status: string; data: OverdueSupplier[] }>(
    '/purchasing/orders/overdue-suppliers/'
  );
  return data.data;
}
