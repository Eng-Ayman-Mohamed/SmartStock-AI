import { useState } from 'react';
import { AlertTriangle, Info, X } from 'lucide-react';
import type { AlertInfo } from '../utils/classifyAlert';

interface AlertBannerProps {
  alert: AlertInfo;
  onDismiss: (id: string) => void;
}

export default function AlertBanner({ alert, onDismiss }: AlertBannerProps) {
  const [isExiting, setIsExiting] = useState(false);
  const isCritical = alert.severity === 'critical';

  const handleDismiss = () => {
    setIsExiting(true);
  };

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm transition-all duration-200 ease-out ${
        isExiting
          ? 'opacity-0 translate-x-4 max-h-0 py-0 mb-0 overflow-hidden border-transparent'
          : 'animate-slideUp'
      } ${
        isCritical
          ? 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/30 dark:border-red-800 dark:text-red-200'
          : 'bg-orange-50 border-orange-200 text-orange-800 dark:bg-orange-900/30 dark:border-orange-800 dark:text-orange-200'
      }`}
      onTransitionEnd={(e) => {
        if (e.propertyName === 'opacity' && isExiting) {
          onDismiss(alert.sku.id);
        }
      }}
    >
      {isCritical ? (
        <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
      ) : (
        <Info className="w-5 h-5 shrink-0 mt-0.5" />
      )}
      <p className="text-sm flex-1">{alert.message}</p>
      <button
        onClick={handleDismiss}
        className="shrink-0 p-0.5 rounded hover:bg-gray-800/60 dark:hover:bg-white/10 transition-colors"
        aria-label="Dismiss alert"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
