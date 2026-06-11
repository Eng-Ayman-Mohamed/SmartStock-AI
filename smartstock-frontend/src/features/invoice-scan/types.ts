export type InvoiceFieldKey =
  | 'product_name'
  | 'sku_code'
  | 'quantity_received'
  | 'unit_price'
  | 'supplier_name';

export type InvoiceStatus = 'pending' | 'extracted' | 'partial' | 'failed' | 'confirmed' | 'rejected';

export type InvoiceFields = Record<InvoiceFieldKey, string | number | null>;

export type InvoiceConfidence = Partial<Record<InvoiceFieldKey, number>>;

export interface InvoiceScanResult {
  scan_id: number;
  status: InvoiceStatus;
  extracted_data: Partial<InvoiceFields>;
  confidence: InvoiceConfidence;
  missing_fields: InvoiceFieldKey[];
  failure_reason?: string;
  confirmed_data?: Record<string, unknown>;
  is_confirmed: boolean;
  inventory_result?: {
    product_id?: number;
    sku_id?: number;
    stock_level_id?: number;
    quantity_on_hand?: number;
    created_product?: boolean;
    created_sku?: boolean;
    created_stock_level?: boolean;
  };
}

export type ConfirmInvoicePayload = {
  scan_id: number;
  confirmed_data: InvoiceFields;
};
