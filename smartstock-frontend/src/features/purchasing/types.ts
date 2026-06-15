export interface Supplier {
  id: number;
  name: string;
  contact_email: string;
  contact_phone: string;
  address: string;
  default_lead_time_days: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateSupplierPayload {
  name: string;
  contact_email: string;
  contact_phone?: string;
  address?: string;
  default_lead_time_days: number;
  is_active: boolean;
}

export type UpdateSupplierPayload = Partial<CreateSupplierPayload>;

export type POStatus = 'draft' | 'pending_approval' | 'approved' | 'email_sent' | 'sent' | 'waiting_confirmation' | 'confirmed' | 'rejected' | 'cancelled' | 'failed' | 'timeout';

export interface PendingPO {
  id: string;
  product: string;
  sku: string;
  supplier: string;
  predicted_stockout: string;
  recommended_qty: number;
  unit_cost: number;
  estimated_total_cost: string;
  agent_reasoning: string | null;
}
