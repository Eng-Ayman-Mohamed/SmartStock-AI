import api from '../../lib/axios';
import type {
  Notification,
  NotificationListParams,
  UnreadCountResponse,
} from './types';

export async function getNotifications(
  params?: NotificationListParams,
): Promise<PaginatedResponse<Notification>> {
  const res = await api.get('/notifications/', { params });
  // ResponseEnvelopeRenderer unwraps paginated responses:
  // res.data = results array, res._meta = {total, page, per_page, next, previous}
  return {
    results: Array.isArray(res.data) ? res.data : (res.data?.results ?? []),
    count: (res._meta?.total as number) ?? 0,
    next: (res._meta?.next as string) ?? null,
    previous: (res._meta?.previous as string) ?? null,
  };
}

export async function getUnreadCount(): Promise<UnreadCountResponse> {
  const res = await api.get<UnreadCountResponse>('/notifications/unread-count/');
  return res.data;
}

export async function markNotificationRead(id: number): Promise<void> {
  await api.post(`/notifications/${id}/mark_read/`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await api.post('/notifications/mark_all_read/');
}

export async function dismissNotification(id: number): Promise<void> {
  await api.post(`/notifications/${id}/dismiss/`);
}
