import { useState } from 'react';
import { Upload, FileText, Check, X, AlertTriangle, Sparkles, Scan } from 'lucide-react';
import Card from '../../../shared/components/Card';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import EmptyState from '../../../shared/components/EmptyState';

export default function InvoiceScanPage() {
  const [uploaded, setUploaded] = useState(false);

  const handleUpload = () => {
    setUploaded(true);
  };

  const fields = [
    { label: 'Product Name', value: 'Wireless Mouse', confidence: 95 },
    { label: 'SKU Code', value: 'WM-2024-001', confidence: 98 },
    { label: 'Quantity', value: '200', confidence: 92 },
    { label: 'Unit Price', value: '$21.25', confidence: 88 },
    { label: 'Supplier Name', value: 'TechSupply Co.', confidence: 85 },
  ];

  const confidenceColor = (pct: number) => {
    if (pct >= 90) return 'text-green-600 bg-green-50';
    if (pct >= 70) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const confidenceDot = (pct: number) => {
    if (pct >= 90) return 'bg-green-600';
    if (pct >= 70) return 'bg-orange-600';
    return 'bg-red-600';
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-page-heading text-ink">Invoice Scan</h1>
          <p className="text-body text-ink-muted mt-1">Drop an invoice, we'll do the paperwork — AI extracts product details automatically</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          {!uploaded ? (
            <button
              type="button"
              className="flex flex-col items-center justify-center py-16 w-full border-2 border-dashed border-hairline rounded-lg cursor-pointer hover:border-brand-200 hover:bg-brand-50/30 transition-colors"
              onClick={handleUpload}
              aria-label="Upload invoice"
            >
              <Upload className="w-12 h-12 text-ink-faint mb-4" />
              <h3 className="text-card-title text-ink-secondary mb-1">Upload Invoice</h3>
              <p className="text-body text-ink-muted text-center max-w-[280px] mb-4">
                Drop an invoice PDF or image here, or click to browse
              </p>
              <Button variant="primary" size="md"><Upload className="w-4 h-4" /> Select File</Button>
              </button>
            ) : (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="w-full max-w-sm rounded-lg border border-hairline bg-canvas-soft p-2 mb-4">
                <div className="aspect-[3/4] rounded-md bg-canvas flex items-center justify-center">
                  <FileText className="w-16 h-16 text-hairline" />
                </div>
              </div>
              <p className="text-body text-ink-muted">invoice_techsupply_20250601.pdf</p>
              <Badge variant="AI Generated">AI Generated</Badge>
            </div>
          )}
        </Card>

        <Card title="Extracted Fields" subtitle={uploaded ? 'Review and confirm before adding to inventory' : 'Upload an invoice to see extracted data'} action={<Button variant="ghost" size="sm"><Sparkles className="w-4 h-4" /> Re-scan</Button>}>
          {!uploaded ? (
            <EmptyState
              icon={Scan}
              heading="No invoices yet"
              body="Upload a supplier invoice and the AI will pull out the product names, SKUs, quantities, and prices."
            />
          ) : (
            <>
              <div className="space-y-4">
                {fields.map((field) => (
                  <div key={field.label}>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-caption text-ink-muted">{field.label}</label>
                      <span className={`inline-flex items-center gap-1 text-caption px-1.5 py-0.5 rounded-sm ${confidenceColor(field.confidence)}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${confidenceDot(field.confidence)}`} />
                        {field.confidence}%
                        {field.confidence < 70 && <span className="text-red-600">Please verify</span>}
                      </span>
                    </div>
                    <input
                      type="text"
                      defaultValue={field.value}
                      className="w-full h-9 px-3 rounded-md border border-hairline bg-canvas text-body text-ink hover:border-ink-muted focus:border-brand-600 focus:outline-none transition-colors"
                      aria-label={field.label}
                    />
                    {field.confidence < 70 && (
                      <p className="text-caption text-red-600 mt-1 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> Low confidence — please verify this value
                      </p>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-3 mt-6 pt-4 border-t border-hairline">
                <Button variant="secondary" size="md" className="flex-1"><X className="w-4 h-4" /> Reject</Button>
                <Button variant="primary" size="md" className="flex-1"><Check className="w-4 h-4" /> Confirm &amp; Add</Button>
              </div>

              <p className="text-caption text-ink-faint text-center mt-3">
                This action will be logged with your user ID and timestamp.
              </p>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
