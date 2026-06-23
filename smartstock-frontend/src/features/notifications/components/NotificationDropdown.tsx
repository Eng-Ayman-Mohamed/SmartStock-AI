import { useNotifications } from "../hooks/useNotifications";
import { useNotificationActions } from "../hooks/useNotificationActions";
import NotificationItem from "./NotificationItem";
import NotificationEmpty from "./NotificationEmpty";
import { Link } from "react-router-dom";

interface Props {
  onClose: () => void;
}

export default function NotificationDropdown({ onClose }: Props) {
  const { data, isLoading } = useNotifications({ page_size: 10 });
  const { markAllRead } = useNotificationActions();
  const notifications = data?.results ?? [];

  return (
    <div className="absolute right-0 mt-2 w-[calc(100vw-2rem)] sm:w-96 bg-canvas rounded-xl shadow-elevated border border-hairline z-50">
      <div className="flex items-center justify-between px-4 py-3 border-b border-hairline">
        <h3 className="text-section-heading text-ink">Notifications</h3>
        {notifications.length > 0 && (
          <button
            onClick={() => markAllRead.mutate()}
            className="text-caption text-brand-600 hover:text-brand-800"
          >
            Mark all read
          </button>
        )}
      </div>
      <div className="max-h-[min(24rem,60vh)] overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-body text-ink-muted">Loading...</div>
        ) : notifications.length === 0 ? (
          <NotificationEmpty />
        ) : (
          notifications.map((n) => (
            <NotificationItem key={n.id} notification={n} onClose={onClose} />
          ))
        )}
      </div>
      <div className="px-4 py-3 border-t border-hairline">
        <Link
          to="/notifications"
          onClick={onClose}
          className="block text-center text-caption text-brand-600 hover:text-brand-800"
        >
          View all notifications
        </Link>
      </div>
    </div>
  );
}
