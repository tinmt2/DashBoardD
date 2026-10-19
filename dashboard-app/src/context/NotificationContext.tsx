import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { 
  SyncNotificationItem, 
  CreateNotificationPayload 
} from '../types/notification';
import { 
  fetchNotifications, 
  recordNotification, 
  markNotificationRead, 
  markAllNotificationsRead, 
  deleteNotification, 
  clearAllNotifications 
} from '../services/notificationService';

interface NotificationContextType {
  notifications: SyncNotificationItem[];
  unreadCount: number;
  loading: boolean;
  isPanelOpen: boolean;
  openPanel: () => void;
  closePanel: () => void;
  togglePanel: () => void;
  refreshNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  removeNotification: (id: string) => Promise<void>;
  removeAllNotifications: () => Promise<void>;
  addNotification: (payload: CreateNotificationPayload) => Promise<SyncNotificationItem | null>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<SyncNotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [isPanelOpen, setIsPanelOpen] = useState<boolean>(false);

  const refreshNotifications = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetchNotifications(50, 0, false);
      if (res.success) {
        setNotifications(res.items || []);
        setUnreadCount(res.unread_count || 0);
      }
    } catch {
      // Yên lặng bỏ qua lỗi mạng khi backend đang offline hoặc khởi động
    } finally {
      setLoading(false);
    }
  }, []);

  // Polling nhẹ mỗi 45s
  useEffect(() => {
    refreshNotifications();
    const interval = setInterval(() => {
      refreshNotifications();
    }, 45000);
    return () => clearInterval(interval);
  }, [refreshNotifications]);

  const openPanel = useCallback(() => setIsPanelOpen(true), []);
  const closePanel = useCallback(() => setIsPanelOpen(false), []);
  const togglePanel = useCallback(() => setIsPanelOpen(prev => !prev), []);

  const markAsRead = useCallback(async (id: string) => {
    try {
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
      await markNotificationRead(id);
    } catch (e) {
      console.error('Lỗi khi đánh dấu đã đọc:', e);
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      await markAllNotificationsRead();
    } catch (e) {
      console.error('Lỗi khi đánh dấu tất cả đã đọc:', e);
    }
  }, []);

  const removeNotification = useCallback(async (id: string) => {
    try {
      const target = notifications.find(n => n.id === id);
      setNotifications(prev => prev.filter(n => n.id !== id));
      if (target && !target.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
      await deleteNotification(id);
    } catch (e) {
      console.error('Lỗi khi xoá thông báo:', e);
    }
  }, [notifications]);

  const removeAllNotifications = useCallback(async () => {
    try {
      setNotifications([]);
      setUnreadCount(0);
      await clearAllNotifications();
    } catch (e) {
      console.error('Lỗi khi xoá tất cả thông báo:', e);
    }
  }, []);

  const addNotification = useCallback(async (payload: CreateNotificationPayload) => {
    try {
      const item = await recordNotification(payload);
      setNotifications(prev => [item, ...prev]);
      setUnreadCount(prev => prev + 1);
      return item;
    } catch (e) {
      console.error('Lỗi khi ghi nhận thông báo:', e);
      return null;
    }
  }, []);

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        loading,
        isPanelOpen,
        openPanel,
        closePanel,
        togglePanel,
        refreshNotifications,
        markAsRead,
        markAllAsRead,
        removeNotification,
        removeAllNotifications,
        addNotification
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};
