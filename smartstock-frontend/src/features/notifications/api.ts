import api from '../../lib/axios';
import type {
  Notification,
  NotificationListParams,
  UnreadCountResponse,
} from './types';

export async function getNotifications(
  params?: NotificationListParams,
): Promise<PaginatedResponse<Notification>> {
  const res = await api.get<PaginatedResponse<Notification>>('/notifications/', { params });
  return res.data;
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
