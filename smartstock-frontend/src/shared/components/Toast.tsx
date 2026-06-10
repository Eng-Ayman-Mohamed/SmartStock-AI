import { CheckCircle, XCircle, Info, X } from 'lucide-react';
import { useToastStore, type ToastType } from '../../store/toastStore';

const iconMap: Record<ToastType, typeof CheckCircle> = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
};

const colorMap: Record<ToastType, string> = {
  success: 'border-l-green-600 bg-green-50 text-green-800',
  error: 'border-l-red-600 bg-red-50 text-red-800',
  info: 'border-l-brand-600 bg-brand-50 text-brand-800',
};

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const removeToast = useToastStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((toast) => {
        const Icon = iconMap[toast.type];
        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-lg border border-hairline shadow-soft border-l-[3px] animate-slideUp ${colorMap[toast.type]}`}
            role="alert"
          >
            <Icon className="w-4 h-4 mt-0.5 shrink-0" aria-hidden="true" />
            <p className="text-body flex-1">{toast.message}</p>
            <button
              onClick={() => removeToast(toast.id)}
              className="shrink-0 flex items-center justify-center w-5 h-5 rounded-full hover:bg-black/5 transition-colors"
              aria-label="Dismiss notification"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
