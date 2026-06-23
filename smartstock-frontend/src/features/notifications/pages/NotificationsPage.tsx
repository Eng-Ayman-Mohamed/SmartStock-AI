import { useState } from "react";
import { useNotifications } from "../hooks/useNotifications";
import { useNotificationActions } from "../hooks/useNotificationActions";
import NotificationItem from "../components/NotificationItem";
import NotificationFilters from "../components/NotificationFilters";
import NotificationEmpty from "../components/NotificationEmpty";
import Button from "../../../shared/components/Button";
import type { NotificationType, NotificationSeverity } from "../types";

export default function NotificationsPage() {
  const [filters, setFilters] = useState<{
    type?: NotificationType;
    severity?: NotificationSeverity;
    date_from?: string;
    date_to?: string;
  }>({});
  const [page, setPage] = useState(1);
  const { data, isLoading } = useNotifications({ ...filters, page, page_size: 20 });
  const { markAllRead } = useNotificationActions();
  const notifications = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const totalPages = Math.ceil(totalCount / 20);

  return (
    <div className="space-y-6 animate-fadeIn flex-1 min-h-0 flex flex-col">
      <div className="flex items-center justify-between">
        <h1 className="text-page-heading text-ink">Notifications</h1>
        {notifications.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => markAllRead.mutate()}
          >
            Mark all read
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <aside className="lg:col-span-1">
          <NotificationFilters filters={filters} onChange={(f) => { setFilters(f); setPage(1); }} />
        </aside>

        <main className="lg:col-span-3">
          {isLoading ? (
            <div className="text-center py-8 text-body text-ink-muted">Loading...</div>
          ) : notifications.length === 0 ? (
            <NotificationEmpty />
          ) : (
            <>
              <div className="bg-canvas rounded-xl border border-hairline divide-y divide-hairline">
                {notifications.map((n) => (
                  <NotificationItem key={n.id} notification={n} onClose={() => {}} />
                ))}
              </div>
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-4 mt-6">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <span className="text-caption text-ink-muted">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}