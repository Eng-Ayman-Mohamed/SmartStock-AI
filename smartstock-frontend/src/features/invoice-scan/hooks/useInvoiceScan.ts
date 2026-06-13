import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { useToastStore } from '../../../store/toastStore';
import * as invoiceScanApi from '../api';
import type { ConfirmInvoicePayload } from '../types';

function errorMessage(err: unknown, fallback: string) {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { message?: string; detail?: string; errors?: unknown } | undefined;
    return data?.message || data?.detail || fallback;
  }
  return fallback;
}

export function useInvoiceScan() {
  const addToast = useToastStore((s) => s.addToast);

  const scan = useMutation({
    mutationFn: (file: File) => invoiceScanApi.scanInvoice(file),
    onSuccess: (result) => {
      if (result.status === 'partial') {
        addToast('Invoice scanned with missing fields. Please verify before confirming.', 'info');
        return;
      }
      addToast('Invoice scanned successfully.', 'success');
    },
    onError: (err) => {
      addToast(errorMessage(err, 'Failed to scan invoice.'), 'error');
    },
  });

  const confirm = useMutation({
    mutationFn: (payload: ConfirmInvoicePayload) => invoiceScanApi.confirmInvoiceScan(payload),
    onSuccess: () => {
      addToast('Invoice confirmed and inventory updated.', 'success');
    },
    onError: (err) => {
      addToast(errorMessage(err, 'Failed to confirm invoice.'), 'error');
    },
  });

  const reject = useMutation({
    mutationFn: (scanId: number) => invoiceScanApi.rejectInvoiceScan(scanId),
    onSuccess: () => {
      addToast('Invoice scan rejected.', 'info');
    },
    onError: (err) => {
      addToast(errorMessage(err, 'Failed to reject invoice scan.'), 'error');
    },
  });

  return {
    scan,
    confirm,
    reject,
    isProcessing: scan.isPending || confirm.isPending || reject.isPending,
  };
}
