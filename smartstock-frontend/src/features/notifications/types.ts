export type NotificationType = "monitoring" | "escalation" | "forecast" | "reorder";
export type NotificationSeverity = "info" | "warning" | "critical";

export interface Notification {
  id: number;
  type: NotificationType;
  severity: NotificationSeverity;
  title: string;
  message: string;
  metadata: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationListParams {
  type?: NotificationType;
  severity?: NotificationSeverity;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface UnreadCountResponse {
  count: number;
}
