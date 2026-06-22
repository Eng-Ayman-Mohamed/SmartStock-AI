export type InvoiceFieldKey =
  | 'product_name'
  | 'sku_code'
  | 'quantity_received'
  | 'unit_price'
  | 'supplier_name';

export type InvoiceHeaderKey =
  | 'supplier_name'
  | 'invoice_number'
  | 'invoice_date'
  | 'due_date'
  | 'invoice_total'
  | 'tax_amount'
  | 'currency';

export type InvoiceStatus = 'pending' | 'extracted' | 'partial' | 'failed' | 'confirmed' | 'rejected';

export type InvoiceHeaderFields = Record<InvoiceHeaderKey, string | number | null>;

export interface InvoiceLineItem {
  item_name: string;
  sku_code: string;
  quantity: number | string;
  unit_price: number | string | null;
  total_price: number | string | null;
}

/** Confidence is keyed by header/legacy field name plus the overall 'line_items' score. */
export type InvoiceConfidence = Record<string, number>;

export interface InvoiceExtractedData extends Partial<InvoiceHeaderFields> {
  line_items?: InvoiceLineItem[];
  // Legacy mirror fields (single-product scans).
  product_name?: string | number | null;
  sku_code?: string | number | null;
  quantity_received?: string | number | null;
  unit_price?: string | number | null;
}

export interface InvoiceInventoryLine {
  item_name?: string;
  sku_code?: string;
  product_id?: number;
  sku_id?: number;
  stock_level_id?: number;
  quantity_added?: number;
  quantity_on_hand?: number;
}

export interface InvoiceInventoryResult {
  lines?: InvoiceInventoryLine[];
  lines_processed?: number;
  lines_failed?: { sku_code?: string; error?: string }[];
  // Legacy single-line shape:
  product_id?: number;
  sku_id?: number;
  stock_level_id?: number;
  quantity_on_hand?: number;
}

export interface InvoiceScanResult {
  scan_id: number;
  status: InvoiceStatus;
  extracted_data: InvoiceExtractedData;
  confidence: InvoiceConfidence;
  missing_fields: string[];
  failure_reason?: string;
  confirmed_data?: Record<string, unknown>;
  is_confirmed: boolean;
  inventory_result?: InvoiceInventoryResult;
}

export interface ConfirmInvoiceData extends Partial<InvoiceHeaderFields> {
  supplier_name: string;
  line_items: InvoiceLineItem[];
}

export type ConfirmInvoicePayload = {
  scan_id: number;
  confirmed_data: ConfirmInvoiceData;
};
