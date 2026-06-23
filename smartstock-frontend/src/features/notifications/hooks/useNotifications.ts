import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../../store/authStore";
import { getNotifications } from "../api";
import { notificationKeys } from "../queryKeys";
import type { NotificationListParams } from "../types";

export function useNotifications(params?: NotificationListParams) {
  const token = useAuthStore((s) => s.token);

  return useQuery({
    queryKey: notificationKeys.list(params),
    queryFn: () => getNotifications(params),
    enabled: !!token,
    retry: false,
  });
}
