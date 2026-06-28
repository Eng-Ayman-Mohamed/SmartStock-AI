import { useMemo, useRef, useState, useEffect } from 'react';
import {
  Check,
  FileText,
  Image as ImageIcon,
  Loader2,
  RotateCcw,
  ShieldCheck,
  Upload,
  X,
} from 'lucide-react';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import EmptyState from '../../../shared/components/EmptyState';
import { useInvoiceScan } from '../hooks/useInvoiceScan';
import { useToastStore } from '../../../store/toastStore';
import InvoiceHeaderForm from '../components/InvoiceHeaderForm';
import LineItemsTable from '../components/LineItemsTable';
import type {
  ConfirmInvoiceData,
  InvoiceHeaderFields,
  InvoiceHeaderKey,
  InvoiceLineItem,
  InvoiceScanResult,
} from '../types';

const MAX_FILE_SIZE = 5 * 1024 * 1024;
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'application/pdf'];

const EMPTY_HEADER: InvoiceHeaderFields = {
  supplier_name: '',
  invoice_number: '',
  invoice_date: '',
  due_date: '',
  invoice_total: '',
  tax_amount: '',
  currency: '',
};

const HEADER_KEYS = Object.keys(EMPTY_HEADER) as InvoiceHeaderKey[];

type Preview =
  | { kind: 'image'; url: string; name: string }
  | { kind: 'pdf'; name: string }
  | null;

function formatBytes(bytes: number) {
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function validateFile(file: File) {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return 'Accepted formats are JPEG, PNG, and PDF.';
  }
  if (file.size > MAX_FILE_SIZE) {
    return 'File size must be 5 MB or less.';
  }
  return '';
}

function normalizeHeader(result: InvoiceScanResult): InvoiceHeaderFields {
  const data = result.extracted_data ?? {};
  return HEADER_KEYS.reduce<InvoiceHeaderFields>((acc, key) => {
    acc[key] = data[key] ?? '';
    return acc;
  }, { ...EMPTY_HEADER });
}

function normalizeLineItems(result: InvoiceScanResult): InvoiceLineItem[] {
  const data = result.extracted_data ?? {};
  if (Array.isArray(data.line_items) && data.line_items.length > 0) {
    return data.line_items.map((line) => ({
      item_name: String(line.item_name ?? ''),
      sku_code: String(line.sku_code ?? ''),
      quantity: line.quantity ?? '',
      unit_price: line.unit_price ?? '',
      total_price: line.total_price ?? '',
    }));
  }
  // Legacy single-product fallback.
  const hasLegacy = data.product_name || data.sku_code || data.quantity_received || data.unit_price;
  if (hasLegacy) {
    return [
      {
        item_name: String(data.product_name ?? ''),
        sku_code: String(data.sku_code ?? ''),
        quantity: data.quantity_received ?? '',
        unit_price: data.unit_price ?? '',
        total_price: '',
      },
    ];
  }
  return [{ item_name: '', sku_code: '', quantity: '', unit_price: '', total_price: '' }];
}

function lineIsComplete(line: InvoiceLineItem) {
  return (
    String(line.item_name ?? '').trim() !== '' &&
    String(line.sku_code ?? '').trim() !== '' &&
    String(line.quantity ?? '').trim() !== '' &&
    Number(line.quantity) >= 1
  );
}

export default function InvoiceScanPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview>(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState('');
  const [scanResult, setScanResult] = useState<InvoiceScanResult | null>(null);
  const [header, setHeader] = useState<InvoiceHeaderFields>(EMPTY_HEADER);
  const [lineItems, setLineItems] = useState<InvoiceLineItem[]>([]);
  const [confirmedResult, setConfirmedResult] = useState<InvoiceScanResult | null>(null);
  const { scan, confirm, reject, isProcessing } = useInvoiceScan();
  const addToast = useToastStore((s) => s.addToast);
  const [errorMessage, setErrorMessage] = useState('');

  const lineConfidence = useMemo(() => scanResult?.confidence?.line_items, [scanResult]);

  useEffect(() => {
    return () => {
      if (preview?.kind === 'image') {
        URL.revokeObjectURL(preview.url);
      }
    };
  }, [preview]);

  function updatePreview(file: File) {
    setPreview((current) => {
      if (current?.kind === 'image') {
        URL.revokeObjectURL(current.url);
      }
      if (file.type === 'application/pdf') {
        return { kind: 'pdf', name: file.name };
      }
      return { kind: 'image', url: URL.createObjectURL(file), name: file.name };
    });
  }

  function resetExtraction() {
    setScanResult(null);
    setHeader(EMPTY_HEADER);
    setLineItems([]);
    setConfirmedResult(null);
  }

  function selectFile(file: File) {
    const error = validateFile(file);
    setFileError(error);
    setErrorMessage('');
    resetExtraction();
    if (error) {
      setSelectedFile(null);
      setPreview((current) => {
        if (current?.kind === 'image') {
          URL.revokeObjectURL(current.url);
        }
        return null;
      });
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }
    setSelectedFile(file);
    updatePreview(file);
  }

  async function scanSelectedFile(file: File) {
    try {
      const result = await scan.mutateAsync(file);
      setScanResult(result);
      setHeader(normalizeHeader(result));
      setLineItems(normalizeLineItems(result));
    } catch {
      resetExtraction();
      setErrorMessage('Failed to scan invoice. Please try again.');
    }
  }

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    selectFile(file);
    const error = validateFile(file);
    if (!error) {
      void scanSelectedFile(file);
    }
  }

  function resetFlow() {
    setSelectedFile(null);
    setPreview((current) => {
      if (current?.kind === 'image') {
        URL.revokeObjectURL(current.url);
      }
      return null;
    });
    setFileError('');
    setErrorMessage('');
    resetExtraction();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  function handleHeaderChange(key: InvoiceHeaderKey, value: string) {
    setHeader((current) => ({ ...current, [key]: value }));
  }

  async function confirmScan() {
    if (!scanResult) return;
    const confirmedData: ConfirmInvoiceData = {
      ...header,
      supplier_name: String(header.supplier_name ?? '').trim(),
      line_items: lineItems,
    };
    try {
      const result = await confirm.mutateAsync({
        scan_id: scanResult.scan_id,
        confirmed_data: confirmedData,
      });
      setScanResult(result);
      setConfirmedResult(result);
    } catch {
      setConfirmedResult(null);
      setErrorMessage('Failed to confirm scan. Please try again.');
    }
  }

  async function rejectScan() {
    if (!scanResult) {
      resetFlow();
      return;
    }
    try {
      await reject.mutateAsync(scanResult.scan_id);
      resetFlow();
    } catch {
      addToast('Failed to reject scan', 'error');
      setErrorMessage('Failed to reject scan. Please try again.');
    }
  }

  const supplierFilled = String(header.supplier_name ?? '').trim() !== '';
  const linesValid = lineItems.length > 0 && lineItems.every(lineIsComplete);
  const canConfirm = Boolean(scanResult) && !isProcessing && supplierFilled && linesValid;

  const inventoryResult = confirmedResult?.inventory_result;

  return (
    <div className="space-y-6 animate-fadeIn pb-20 md:pb-0">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-page-heading text-ink">Invoice Scan</h1>
          <p className="text-body text-ink-muted mt-1">
            Upload a supplier invoice, verify the AI extraction, then add the received stock.
          </p>
        </div>
        <Button
          variant="secondary"
          size="md"
          onClick={resetFlow}
          disabled={isProcessing || (!selectedFile && !scanResult)}
        >
          <RotateCcw className="w-4 h-4" /> Reset
        </Button>
      </div>

      {errorMessage && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800 dark:border-red-800 dark:bg-red-900/30 dark:text-red-200">
          {errorMessage}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] gap-6 items-start">
        <Card title="Original Upload" subtitle="JPEG, PNG, or PDF. Maximum 5 MB.">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,application/pdf,.jpg,.jpeg,.png,.pdf"
            className="sr-only"
            onChange={(event) => handleFiles(event.target.files)}
          />

          <button
            type="button"
            className={`flex w-full flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-12 text-center transition-colors ${
              dragActive ? 'border-brand-600 bg-brand-50' : 'border-hairline bg-canvas hover:border-brand-200 hover:bg-brand-50/30'
            }`}
            onClick={() => fileInputRef.current?.click()}
            onDragEnter={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={(event) => {
              event.preventDefault();
              setDragActive(false);
            }}
            onDrop={(event) => {
              event.preventDefault();
              setDragActive(false);
              handleFiles(event.dataTransfer.files);
            }}
            disabled={isProcessing}
            aria-label="Upload invoice"
          >
            {scan.isPending ? (
              <Loader2 className="w-12 h-12 text-brand-600 mb-4 animate-spin" />
            ) : (
              <Upload className="w-12 h-12 text-ink-faint mb-4" />
            )}
            <span className="text-card-title text-ink-secondary">Drop invoice here</span>
            <span className="text-body text-ink-muted mt-1 max-w-[320px]">
              Click to browse or drag in a file. PDFs are processed from the first page.
            </span>
            <span className="mt-4 inline-flex items-center justify-center gap-2 rounded-full bg-brand-600 px-4 py-2 text-body font-medium text-white">
              <Upload className="w-4 h-4" /> Select File
            </span>
          </button>

          {fileError && (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800 dark:border-red-800 dark:bg-red-900/30 dark:text-red-200">
              {fileError}
            </div>
          )}

          {selectedFile && (
            <div className="mt-5 space-y-3">
              <div className="flex items-center justify-between gap-3 rounded-md border border-hairline bg-canvas-soft px-4 py-3">
                <div className="flex min-w-0 items-center gap-3">
                  {preview?.kind === 'pdf' ? (
                    <FileText className="w-5 h-5 shrink-0 text-brand-600" />
                  ) : (
                    <ImageIcon className="w-5 h-5 shrink-0 text-brand-600" />
                  )}
                  <div className="min-w-0">
                    <p className="truncate text-body font-medium text-ink">{selectedFile.name}</p>
                    <p className="text-caption text-ink-muted">{formatBytes(selectedFile.size)}</p>
                  </div>
                </div>
                {scan.isPending && <span className="text-caption text-brand-700">Scanning...</span>}
              </div>

              <div className="rounded-lg border border-hairline bg-canvas-soft p-2">
                <div className="flex aspect-[4/5] items-center justify-center overflow-hidden rounded-md bg-canvas">
                  {preview?.kind === 'image' ? (
                    <img src={preview.url} alt="Uploaded invoice preview" className="h-full w-full object-contain" loading="lazy" />
                  ) : (
                    <div className="flex flex-col items-center gap-3 text-ink-muted">
                      <FileText className="w-16 h-16 text-hairline" />
                      <span className="text-body">PDF first page will be scanned</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </Card>

        <Card
          title="Extracted Invoice"
          subtitle={scanResult ? 'Review the header and line items before confirming.' : 'Upload an invoice to extract its details.'}
        >
          {!scanResult ? (
            <EmptyState
              icon={FileText}
              heading={scan.isPending ? 'Reading invoice' : 'No scan yet'}
              body={
                scan.isPending
                  ? 'The Vision API is extracting the invoice header and line items now.'
                  : 'Upload a supplier invoice to extract the supplier, invoice details, and every line item.'
              }
            />
          ) : (
            <div className="space-y-6">
              {scanResult.status === 'partial' && (
                <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-body text-amber-900 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
                  Some values were missing from the scan. Fill them in before confirming.
                </div>
              )}

              <InvoiceHeaderForm
                header={header}
                confidence={scanResult.confidence ?? {}}
                onChange={handleHeaderChange}
              />

              <LineItemsTable items={lineItems} lineConfidence={lineConfidence} onChange={setLineItems} />

              {inventoryResult && (
                <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-body text-green-900 dark:border-green-800 dark:bg-green-900/30 dark:text-green-200">
                  <p className="font-medium">
                    {inventoryResult.lines_processed ?? inventoryResult.lines?.length ?? 0} line item(s) added to inventory.
                  </p>
                  {inventoryResult.lines_failed && inventoryResult.lines_failed.length > 0 && (
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-caption text-amber-800 dark:text-amber-300">
                      {inventoryResult.lines_failed.map((failed, index) => (
                        <li key={`${failed.sku_code}-${index}`}>
                          {failed.sku_code || 'Line'}: {failed.error}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              <div className="flex flex-col gap-3 border-t border-hairline pt-4 sm:flex-row">
                <Button variant="secondary" size="md" className="flex-1" onClick={rejectScan} disabled={isProcessing}>
                  <X className="w-4 h-4" /> Reject
                </Button>
                <Button variant="primary" size="md" className="flex-1" onClick={confirmScan} disabled={!canConfirm}>
                  {confirm.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  Confirm &amp; Add to Inventory
                </Button>
              </div>

              <div className="flex items-start gap-2 rounded-md bg-canvas-soft px-3 py-2 text-caption text-ink-muted">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-green-700" />
                <span>Confirmation is audited with the original extraction, your edited values, user ID, and timestamp.</span>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
