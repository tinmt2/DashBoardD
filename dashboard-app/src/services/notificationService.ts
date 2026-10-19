import { 
  NotificationListResponse, 
  CreateNotificationPayload, 
  SyncNotificationItem 
} from '../types/notification';

const API_BASE_URL = import.meta.env.VITE_API_URL || (
  window.location.protocol === 'file:' 
    ? 'http://127.0.0.1:8000' 
    : (window.location.port === '5174' ? `http://${window.location.hostname}:8000` : window.location.origin)
);

export const fetchNotifications = async (
  limit = 50, 
  skip = 0, 
  unreadOnly = false,
  signal?: AbortSignal
): Promise<NotificationListResponse> => {
  const params = new URLSearchParams({
    limit: limit.toString(),
    skip: skip.toString(),
    unread_only: unreadOnly ? 'true' : 'false'
  });

  const response = await fetch(`${API_BASE_URL}/api/notifications?${params.toString()}`, { signal });
  if (!response.ok) {
    throw new Error('Không thể tải danh sách thông báo');
  }
  return response.json();
};

export const recordNotification = async (
  payload: CreateNotificationPayload,
  signal?: AbortSignal
): Promise<SyncNotificationItem> => {
  const response = await fetch(`${API_BASE_URL}/api/notifications`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload),
    signal
  });

  if (!response.ok) {
    throw new Error('Không thể ghi nhận thông báo đồng bộ');
  }
  const data = await response.json();
  return data.item;
};

export const markNotificationRead = async (
  notificationId: string,
  signal?: AbortSignal
): Promise<SyncNotificationItem> => {
  const response = await fetch(`${API_BASE_URL}/api/notifications/${notificationId}/read`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json'
    },
    signal
  });

  if (!response.ok) {
    throw new Error('Không thể đánh dấu đã đọc thông báo');
  }
  const data = await response.json();
  return data.item;
};

export const markAllNotificationsRead = async (signal?: AbortSignal): Promise<number> => {
  const response = await fetch(`${API_BASE_URL}/api/notifications/mark-all-read`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    signal
  });

  if (!response.ok) {
    throw new Error('Không thể đánh dấu tất cả đã đọc');
  }
  const data = await response.json();
  return data.updated;
};

export const deleteNotification = async (
  notificationId: string,
  signal?: AbortSignal
): Promise<boolean> => {
  const response = await fetch(`${API_BASE_URL}/api/notifications/${notificationId}`, {
    method: 'DELETE',
    signal
  });

  if (!response.ok) {
    throw new Error('Không thể xoá thông báo');
  }
  return true;
};

export const clearAllNotifications = async (signal?: AbortSignal): Promise<number> => {
  const response = await fetch(`${API_BASE_URL}/api/notifications`, {
    method: 'DELETE',
    signal
  });

  if (!response.ok) {
    throw new Error('Không thể xoá tất cả thông báo');
  }
  const data = await response.json();
  return data.deleted;
};
