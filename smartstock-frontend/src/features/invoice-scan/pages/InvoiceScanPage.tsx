import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertTriangle,
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
import type { InvoiceFieldKey, InvoiceFields, InvoiceScanResult } from '../types';

const MAX_FILE_SIZE = 5 * 1024 * 1024;
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'application/pdf'];

const FIELD_LABELS: Record<InvoiceFieldKey, string> = {
  product_name: 'Product Name',
  sku_code: 'SKU Code',
  quantity_received: 'Quantity Received',
  unit_price: 'Unit Price',
  supplier_name: 'Supplier Name',
};

const FIELD_ORDER = Object.keys(FIELD_LABELS) as InvoiceFieldKey[];

const emptyFields: InvoiceFields = {
  product_name: '',
  sku_code: '',
  quantity_received: '',
  unit_price: '',
  supplier_name: '',
};

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

function normalizeFields(result: InvoiceScanResult): InvoiceFields {
  return FIELD_ORDER.reduce<InvoiceFields>((acc, key) => {
    const value = result.extracted_data?.[key];
    acc[key] = value ?? '';
    return acc;
  }, { ...emptyFields });
}

function confidenceTone(value = 0) {
  if (value >= 0.9) {
    return {
      label: 'High',
      className: 'bg-green-50 text-green-800',
      dot: 'bg-green-600',
    };
  }
  if (value >= 0.7) {
    return {
      label: 'Review',
      className: 'bg-amber-50 text-amber-800',
      dot: 'bg-amber-600',
    };
  }
  return {
    label: 'Please verify',
    className: 'bg-red-50 text-red-800',
    dot: 'bg-red-600',
  };
}

export default function InvoiceScanPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview>(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState('');
  const [scanResult, setScanResult] = useState<InvoiceScanResult | null>(null);
  const [fields, setFields] = useState<InvoiceFields>(emptyFields);
  const [confirmedResult, setConfirmedResult] = useState<InvoiceScanResult | null>(null);
  const { scan, confirm, reject, isProcessing } = useInvoiceScan();

  const missingFields = useMemo(
    () => new Set(scanResult?.missing_fields ?? []),
    [scanResult?.missing_fields],
  );

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

  function selectFile(file: File) {
    const error = validateFile(file);
    setFileError(error);
    setConfirmedResult(null);
    setScanResult(null);
    setFields(emptyFields);
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
      setFields(normalizeFields(result));
    } catch {
      setScanResult(null);
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
    setScanResult(null);
    setFields(emptyFields);
    setConfirmedResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  async function confirmScan() {
    if (!scanResult) return;
    try {
      const result = await confirm.mutateAsync({
        scan_id: scanResult.scan_id,
        confirmed_data: fields,
      });
      setScanResult(result);
      setConfirmedResult(result);
    } catch {
      setConfirmedResult(null);
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
      return;
    }
  }

  const canConfirm = Boolean(scanResult) && !isProcessing && FIELD_ORDER.every((field) => String(fields[field] ?? '').trim());

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-page-heading text-ink">Invoice Scan</h1>
          <p className="text-body text-ink-muted mt-1">
            Upload a supplier invoice, verify the AI extraction, then add the received stock.
          </p>
        </div>
        <Button variant="secondary" size="md" onClick={resetFlow} disabled={isProcessing || (!selectedFile && !scanResult)}>
          <RotateCcw className="w-4 h-4" /> Reset
        </Button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] gap-6 items-start">
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
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-body text-red-800">
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
                    <img src={preview.url} alt="Uploaded invoice preview" className="h-full w-full object-contain" />
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
          title="Extracted Fields"
          subtitle={scanResult ? 'Review every value before confirming.' : 'Upload an invoice to extract product details.'}
        >
          {!scanResult ? (
            <EmptyState
              icon={FileText}
              heading={scan.isPending ? 'Reading invoice' : 'No scan yet'}
              body={
                scan.isPending
                  ? 'The Vision API is extracting invoice fields now.'
                  : 'Upload a supplier invoice to extract product name, SKU, quantity, price, and supplier.'
              }
            />
          ) : (
            <>
              {scanResult.status === 'partial' && (
                <div className="mb-5 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-body text-amber-900">
                  Some fields were missing from the scan. Fill them in before confirming.
                </div>
              )}

              <div className="space-y-4">
                {FIELD_ORDER.map((field) => {
                  const confidence = scanResult.confidence?.[field] ?? 0;
                  const tone = confidenceTone(confidence);
                  const lowConfidence = confidence < 0.7;

                  return (
                    <div key={field}>
                      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                        <label className="text-caption text-ink-muted" htmlFor={`invoice-${field}`}>
                          {FIELD_LABELS[field]}
                        </label>
                        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-eyebrow ${tone.className}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${tone.dot}`} />
                          {Math.round(confidence * 100)}% {tone.label}
                        </span>
                      </div>
                      <input
                        id={`invoice-${field}`}
                        type={field === 'quantity_received' || field === 'unit_price' ? 'number' : 'text'}
                        min={field === 'quantity_received' || field === 'unit_price' ? '0' : undefined}
                        step={field === 'unit_price' ? '0.01' : field === 'quantity_received' ? '1' : undefined}
                        value={String(fields[field] ?? '')}
                        onChange={(event) => setFields((current) => ({ ...current, [field]: event.target.value }))}
                        className={`h-9 w-full rounded-md border bg-canvas px-3 text-body text-ink transition-colors hover:border-ink-muted focus:border-brand-600 focus:outline-none ${
                          missingFields.has(field) || lowConfidence ? 'border-amber-300' : 'border-hairline'
                        }`}
                      />
                      {(missingFields.has(field) || lowConfidence) && (
                        <p className="mt-1 flex items-center gap-1 text-caption text-amber-800">
                          <AlertTriangle className="w-3 h-3" /> Please verify this value.
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>

              {confirmedResult?.inventory_result && (
                <div className="mt-5 rounded-md border border-green-200 bg-green-50 px-4 py-3 text-body text-green-900">
                  Inventory updated. Current on-hand quantity:{' '}
                  <span className="font-medium tabular-nums">
                    {confirmedResult.inventory_result.quantity_on_hand ?? 'updated'}
                  </span>
                </div>
              )}

              <div className="mt-6 flex flex-col gap-3 border-t border-hairline pt-4 sm:flex-row">
                <Button variant="secondary" size="md" className="flex-1" onClick={rejectScan} disabled={isProcessing}>
                  <X className="w-4 h-4" /> Reject
                </Button>
                <Button variant="primary" size="md" className="flex-1" onClick={confirmScan} disabled={!canConfirm}>
                  {confirm.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  Confirm &amp; Add to Inventory
                </Button>
              </div>

              <div className="mt-3 flex items-start gap-2 rounded-md bg-canvas-soft px-3 py-2 text-caption text-ink-muted">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-green-700" />
                <span>Confirmation is audited with the original extraction, your edited values, user ID, and timestamp.</span>
              </div>

              <div className="flex items-start gap-2 rounded-md bg-canvas-soft px-3 py-2 text-caption text-ink-muted">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-green-700" />
                <span>Extracted data is processed by AI and stored securely. PII (emails, phone numbers) is only visible to managers and administrators.</span>
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
