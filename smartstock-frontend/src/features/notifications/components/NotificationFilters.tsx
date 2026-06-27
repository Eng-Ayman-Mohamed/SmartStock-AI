import type { NotificationType, NotificationSeverity } from "../types";
import Input from '../../../shared/components/Input';

interface Props {
  filters: {
    type?: NotificationType;
    severity?: NotificationSeverity;
    date_from?: string;
    date_to?: string;
  };
  onChange: (filters: Props["filters"]) => void;
}

const types: { value: NotificationType; label: string }[] = [
  { value: "monitoring", label: "System" },
  { value: "escalation", label: "Escalation" },
  { value: "forecast", label: "Forecast" },
  { value: "reorder", label: "Inventory" },
];

const severities: { value: NotificationSeverity; label: string }[] = [
  { value: "info", label: "Info" },
  { value: "warning", label: "Warning" },
  { value: "critical", label: "Critical" },
];

export default function NotificationFilters({ filters, onChange }: Props) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-caption font-medium text-ink-secondary mb-2">
          Type
        </label>
        <div className="flex flex-wrap gap-2">
          {types.map((t) => (
            <button
              key={t.value}
              onClick={() =>
                onChange({ ...filters, type: filters.type === t.value ? undefined : t.value })
              }
              className={`px-3 py-2.5 rounded-full text-caption font-medium transition-colors min-h-[44px] ${
                filters.type === t.value
                  ? "bg-brand-600 text-white"
                  : "bg-canvas-soft text-ink-secondary hover:bg-canvas hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-caption font-medium text-ink-secondary mb-2">
          Severity
        </label>
        <div className="flex flex-wrap gap-2">
          {severities.map((s) => (
            <button
              key={s.value}
              onClick={() =>
                onChange({ ...filters, severity: filters.severity === s.value ? undefined : s.value })
              }
              className={`px-3 py-2.5 rounded-full text-caption font-medium transition-colors min-h-[44px] ${
                filters.severity === s.value
                  ? "bg-brand-600 text-white"
                  : "bg-canvas-soft text-ink-secondary hover:bg-canvas hover:text-ink"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-caption font-medium text-ink-secondary mb-2">
          Date Range
        </label>
        <div className="flex flex-col gap-2">
          <Input
            type="date"
            value={filters.date_from ?? ""}
            onChange={(e) => onChange({ ...filters, date_from: e.target.value || undefined })}
            className="flex-1 min-w-0 px-3 py-1.5 rounded-lg border border-hairline bg-canvas text-body text-ink focus:border-brand-600 focus:outline-none transition-colors"
          />
          <Input
            type="date"
            value={filters.date_to ?? ""}
            onChange={(e) => onChange({ ...filters, date_to: e.target.value || undefined })}
            className="flex-1 min-w-0 px-3 py-1.5 rounded-lg border border-hairline bg-canvas text-body text-ink focus:border-brand-600 focus:outline-none transition-colors"
          />
        </div>
      </div>
    </div>
  );
}