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
