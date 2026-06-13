import api from '../../lib/axios';
import type { ConfirmInvoicePayload, InvoiceScanResult } from './types';

type ApiEnvelope<T> = { status?: string; data?: T; message?: string; errors?: unknown };

function unwrap<T>(payload: T | ApiEnvelope<T>): T {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as ApiEnvelope<T>).data as T;
  }
  return payload as T;
}

export async function scanInvoice(file: File): Promise<InvoiceScanResult> {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await api.post<ApiEnvelope<InvoiceScanResult> | InvoiceScanResult>(
    '/ai/invoice-scan/',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return unwrap(data);
}

export async function confirmInvoiceScan(payload: ConfirmInvoicePayload): Promise<InvoiceScanResult> {
  const { data } = await api.post<ApiEnvelope<InvoiceScanResult> | InvoiceScanResult>(
    '/ai/invoice-scan/confirm/',
    payload,
  );
  return unwrap(data);
}

export async function rejectInvoiceScan(scanId: number): Promise<InvoiceScanResult> {
  const { data } = await api.post<ApiEnvelope<InvoiceScanResult> | InvoiceScanResult>(
    `/ai/invoice-scan/${scanId}/reject/`,
  );
  return unwrap(data);
}
