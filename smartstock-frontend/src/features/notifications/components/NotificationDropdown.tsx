import { useNotifications } from "../hooks/useNotifications";
import { useNotificationActions } from "../hooks/useNotificationActions";
import NotificationItem from "./NotificationItem";
import NotificationEmpty from "./NotificationEmpty";
import NotificationSkeleton from "./NotificationSkeleton";
import { Link } from "react-router-dom";

interface Props {
  onClose: () => void;
}

export default function NotificationDropdown({ onClose }: Props) {
  const { data, isLoading } = useNotifications({ page_size: 10 });
  const { markAllRead } = useNotificationActions();
  const notifications = data?.results ?? [];

  return (
    <div className="fixed left-4 right-4 sm:absolute sm:left-auto sm:right-0 mt-2 sm:w-96 bg-canvas rounded-xl shadow-elevated border border-hairline z-[60] max-h-[70vh] overflow-hidden flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-hairline">
        <h3 className="text-section-heading text-ink">Notifications</h3>
        {notifications.length > 0 && (
          <button
            onClick={() => markAllRead.mutate()}
            className="text-caption text-brand-600 hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-200"
          >
            Mark all read
          </button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto min-h-0">
        {isLoading ? (
          <div className="py-2">
            <NotificationSkeleton count={3} />
          </div>
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
          className="block text-center text-caption text-brand-600 hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-200 min-h-[44px] leading-[44px]"
        >
          View all notifications
        </Link>
      </div>
    </div>
  );
}
