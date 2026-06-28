import { ConfidenceBadge } from '../confidence';
import type { InvoiceConfidence, InvoiceHeaderFields, InvoiceHeaderKey } from '../types';
import Input from '../../../shared/components/Input';

type HeaderFieldDef = {
  key: InvoiceHeaderKey;
  label: string;
  type: 'text' | 'date' | 'number';
  required?: boolean;
  wide?: boolean;
};

const HEADER_FIELDS: HeaderFieldDef[] = [
  { key: 'supplier_name', label: 'Supplier', type: 'text', required: true, wide: true },
  { key: 'invoice_number', label: 'Invoice #', type: 'text' },
  { key: 'currency', label: 'Currency', type: 'text' },
  { key: 'invoice_date', label: 'Invoice Date', type: 'date' },
  { key: 'due_date', label: 'Due Date', type: 'date' },
  { key: 'invoice_total', label: 'Invoice Total', type: 'number' },
  { key: 'tax_amount', label: 'Tax / VAT', type: 'number' },
];

interface InvoiceHeaderFormProps {
  header: InvoiceHeaderFields;
  confidence: InvoiceConfidence;
  onChange: (key: InvoiceHeaderKey, value: string) => void;
}

export default function InvoiceHeaderForm({ header, confidence, onChange }: InvoiceHeaderFormProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {HEADER_FIELDS.map(({ key, label, type, required, wide }) => (
        <div key={key} className={wide ? 'sm:col-span-2' : ''}>
          <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
            <label className="text-caption text-ink-muted" htmlFor={`invoice-header-${key}`}>
              {label}
              {required && <span className="text-red-600"> *</span>}
            </label>
            <ConfidenceBadge value={confidence?.[key]} />
          </div>
          <Input
            id={`invoice-header-${key}`}
            type={type}
            inputMode={type === 'number' ? 'decimal' : undefined}
            step={type === 'number' ? '0.01' : undefined}
            min={type === 'number' ? '0' : undefined}
            value={header[key] == null ? '' : String(header[key])}
            onChange={(event) => onChange(key, event.target.value)}
          />
        </div>
      ))}
    </div>
  );
}
