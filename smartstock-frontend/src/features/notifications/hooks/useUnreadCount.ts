import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../../store/authStore";
import { getUnreadCount } from "../api";
import { notificationKeys } from "../queryKeys";

export function useUnreadCount() {
  const token = useAuthStore((s) => s.token);

  return useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: getUnreadCount,
    enabled: !!token,
    refetchInterval: 60_000,
    retry: false,
  });
}
