import { useState, useRef, useEffect } from "react";
import { Bell } from "lucide-react";
import { useUnreadCount } from "../hooks/useUnreadCount";
import NotificationDropdown from "./NotificationDropdown";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { data } = useUnreadCount();
  const count = data?.count ?? 0;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2.5 min-w-[44px] min-h-[44px] rounded-lg hover:bg-canvas-soft transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5 text-ink-muted" />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center w-5 h-5 text-[11px] font-bold text-white bg-red-500 rounded-full">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>
      {open && <NotificationDropdown onClose={() => setOpen(false)} />}
    </div>
  );
}
