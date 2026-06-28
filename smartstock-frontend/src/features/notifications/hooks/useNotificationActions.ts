import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  markNotificationRead,
  markAllNotificationsRead,
  dismissNotification,
} from "../api";
import { notificationKeys } from "../queryKeys";
import type { Notification, UnreadCountResponse } from "../types";

export function useNotificationActions() {
  const qc = useQueryClient();

  const markRead = useMutation({
    mutationFn: markNotificationRead,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: notificationKeys.all });

      const prevLists = qc.getQueriesData<PaginatedResponse<Notification>>({
        queryKey: notificationKeys.lists(),
      });
      const prevUnread = qc.getQueryData<UnreadCountResponse>(
        notificationKeys.unreadCount(),
      );

      qc.setQueriesData<PaginatedResponse<Notification>>(
        { queryKey: notificationKeys.lists() },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            results: old.results.map((n) =>
              n.id === id ? { ...n, is_read: true } : n,
            ),
          };
        },
      );

      if (prevUnread) {
        const wasUnread = prevLists.some(([, data]) =>
          data?.results.some((n) => n.id === id && !n.is_read),
        );
        if (wasUnread) {
          qc.setQueryData<UnreadCountResponse>(
            notificationKeys.unreadCount(),
            (old) => {
              if (!old) return old;
              return { count: Math.max(0, old.count - 1) };
            },
          );
        }
      }

      return { prevLists, prevUnread };
    },
    onError: (_err, _id, context) => {
      if (context?.prevLists) {
        for (const [key, data] of context.prevLists) {
          qc.setQueryData(key, data);
        }
      }
      if (context?.prevUnread) {
        qc.setQueryData(notificationKeys.unreadCount(), context.prevUnread);
      }
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });

  const markAllRead = useMutation({
    mutationFn: markAllNotificationsRead,
    onMutate: async () => {
      await qc.cancelQueries({ queryKey: notificationKeys.all });

      const prevLists = qc.getQueriesData<PaginatedResponse<Notification>>({
        queryKey: notificationKeys.lists(),
      });
      const prevUnread = qc.getQueryData<UnreadCountResponse>(
        notificationKeys.unreadCount(),
      );

      qc.setQueriesData<PaginatedResponse<Notification>>(
        { queryKey: notificationKeys.lists() },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            results: old.results.map((n) => ({ ...n, is_read: true })),
          };
        },
      );

      qc.setQueryData<UnreadCountResponse>(notificationKeys.unreadCount(), {
        count: 0,
      });

      return { prevLists, prevUnread };
    },
    onError: (_err, _variables, context) => {
      if (context?.prevLists) {
        for (const [key, data] of context.prevLists) {
          qc.setQueryData(key, data);
        }
      }
      if (context?.prevUnread) {
        qc.setQueryData(notificationKeys.unreadCount(), context.prevUnread);
      }
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });

  const dismiss = useMutation({
    mutationFn: dismissNotification,
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: notificationKeys.all });

      const prevLists = qc.getQueriesData<PaginatedResponse<Notification>>({
        queryKey: notificationKeys.lists(),
      });
      const prevUnread = qc.getQueryData<UnreadCountResponse>(
        notificationKeys.unreadCount(),
      );

      qc.setQueriesData<PaginatedResponse<Notification>>(
        { queryKey: notificationKeys.lists() },
        (old) => {
          if (!old) return old;
          const wasInResults = old.results.some((n) => n.id === id);
          return {
            ...old,
            results: old.results.filter((n) => n.id !== id),
            count: wasInResults ? old.count - 1 : old.count,
          };
        },
      );

      if (prevUnread) {
        const wasUnread = prevLists.some(([, data]) =>
          data?.results.some((n) => n.id === id && !n.is_read),
        );
        if (wasUnread) {
          qc.setQueryData<UnreadCountResponse>(
            notificationKeys.unreadCount(),
            (old) => (old ? { count: Math.max(0, old.count - 1) } : old),
          );
        }
      }

      return { prevLists, prevUnread };
    },
    onError: (_err, _id, context) => {
      if (context?.prevLists) {
        for (const [key, data] of context.prevLists) {
          qc.setQueryData(key, data);
        }
      }
      if (context?.prevUnread) {
        qc.setQueryData(notificationKeys.unreadCount(), context.prevUnread);
      }
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });

  return { markRead, markAllRead, dismiss };
}
