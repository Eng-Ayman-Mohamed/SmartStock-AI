import { AlertTriangle, Info, X } from 'lucide-react';
import type { AlertInfo } from '../utils/classifyAlert';

interface AlertBannerProps {
  alert: AlertInfo;
  onDismiss: (id: string) => void;
}

export default function AlertBanner({ alert, onDismiss }: AlertBannerProps) {
  const isCritical = alert.severity === 'critical';

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm ${
        isCritical
          ? 'bg-red-50 border-red-200 text-red-800'
          : 'bg-amber-50 border-amber-200 text-amber-800'
      }`}
    >
      {isCritical ? (
        <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
      ) : (
        <Info className="w-5 h-5 shrink-0 mt-0.5" />
      )}
      <p className="text-sm flex-1">{alert.message}</p>
      <button
        onClick={() => onDismiss(alert.sku.id)}
        className="shrink-0 p-0.5 rounded hover:bg-gray-800/60 transition-colors"
        aria-label="Dismiss alert"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
