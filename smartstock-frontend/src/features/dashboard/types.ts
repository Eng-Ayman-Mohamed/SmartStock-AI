export interface ReorderAlert {
  id: number;
  product_id: number;
  product_name: string;
  sku_code: string;
  quantity: number;
  reorder_point: number;
  reorder_quantity: number;
  supplier_name: string | null;
  predicted_stockout_date: string | null;
}

export interface AgentRun {
  id: number;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface PurchaseOrder {
  id: number;
  sku: number;
  sku_code: string;
  product_name: string;
  supplier: number;
  supplier_name: string;
  quantity: number;
  total_cost: string;
  status: string;
  requested_by: number | null;
  requested_by_name: string | null;
  approved_by: number | null;
  approved_by_name: string | null;
  agent_reasoning: string | null;
  notes: string;
  sent_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface OverduePO {
  po_id: number;
  po_number: string;
  sent_at: string;
  deadline: string;
}

export interface OverdueSupplier {
  supplier_id: number;
  supplier_name: string;
  overdue_pos: OverduePO[];
  days_overdue: number;
}
