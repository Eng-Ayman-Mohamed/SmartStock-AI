import { AlertTriangle, Info, AlertCircle } from "lucide-react";
import { useNotificationActions } from "../hooks/useNotificationActions";
import type { Notification, NotificationSeverity } from "../types";

const severityConfig: Record<
  NotificationSeverity,
  { icon: typeof AlertCircle; color: string; bg: string }
> = {
  critical: {
    icon: AlertCircle,
    color: "text-red-600",
    bg: "bg-red-50",
  },
  warning: {
    icon: AlertTriangle,
    color: "text-orange-600",
    bg: "bg-orange-50",
  },
  info: {
    icon: Info,
    color: "text-brand-600",
    bg: "bg-brand-50",
  },
};

const typeLabels: Record<string, string> = {
  monitoring: "System",
  escalation: "Escalation",
  forecast: "Forecast",
  reorder: "Inventory",
};

interface Props {
  notification: Notification;
  onClose: () => void;
}

export default function NotificationItem({ notification, onClose }: Props) {
  const { markRead, dismiss } = useNotificationActions();
  const config = severityConfig[notification.severity];
  const Icon = config.icon;

  const handleClick = () => {
    markRead.mutate(notification.id);
    onClose();
  };

  const handleDismiss = (e: React.MouseEvent) => {
    e.stopPropagation();
    dismiss.mutate(notification.id);
  };

  return (
    <div
      onClick={handleClick}
      className={`flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-canvas-soft transition-colors ${
        !notification.is_read ? config.bg : ""
      }`}
    >
      <div className={`mt-0.5 ${config.color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p
          className={`text-body ${
            !notification.is_read ? "font-semibold text-ink" : "text-ink-secondary"
          }`}
        >
          {notification.title}
        </p>
        <p className="text-caption text-ink-muted truncate">
          {notification.message}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-caption text-ink-faint">
            {typeLabels[notification.type]}
          </span>
          <span className="text-caption text-ink-faint">·</span>
          <time className="text-caption text-ink-faint">
            {new Date(notification.created_at).toLocaleDateString()}
          </time>
        </div>
      </div>
      <button
        onClick={handleDismiss}
        className="text-ink-faint hover:text-ink-muted"
        aria-label="Dismiss"
      >
        <span className="sr-only">Dismiss</span>
        ×
      </button>
    </div>
  );
}
