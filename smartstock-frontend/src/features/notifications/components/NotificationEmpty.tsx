import { Bell } from "lucide-react";

export default function NotificationEmpty() {
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4">
      <Bell className="w-10 h-10 text-ink-faint mb-3" />
      <p className="text-body text-ink-muted">No notifications yet</p>
    </div>
  );
}
