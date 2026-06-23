import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  markNotificationRead,
  markAllNotificationsRead,
  dismissNotification,
} from "../api";
import { notificationKeys } from "../queryKeys";

export function useNotificationActions() {
  const qc = useQueryClient();

  const markRead = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });

  const markAllRead = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });

  const dismiss = useMutation({
    mutationFn: dismissNotification,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });

  return { markRead, markAllRead, dismiss };
}
