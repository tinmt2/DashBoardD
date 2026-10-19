export type NotificationStatus = 'SUCCESS' | 'FAILED' | 'PARTIAL';

export type SyncType = 'SYNC_ALL' | 'FPT_SHOP' | 'LONG_CHAU' | 'VACCINE' | 'IMPORT_EXCEL';

export interface ChainSyncDetail {
  chain: string; // 'FPT Shop' | 'Long Châu' | 'Vaccine'
  status: 'SUCCESS' | 'FAILED';
  new_records: number; // Số lỗi cập nhật được thêm
  total_rows?: number; // Tổng số bản ghi/lỗi quét được
  duplicate_records?: number; // Số bản ghi trùng lặp
  error_message?: string | null;
}

export interface SyncNotificationItem {
  id: string;
  title: string;
  status: NotificationStatus;
  sync_type: SyncType;
  start_date?: string | null;
  end_date?: string | null;
  total_new_errors: number;
  total_scanned: number;
  total_duplicates: number;
  chain_details: ChainSyncDetail[];
  error_message?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface CreateNotificationPayload {
  title: string;
  status: NotificationStatus;
  sync_type: SyncType;
  start_date?: string | null;
  end_date?: string | null;
  total_new_errors: number;
  total_scanned: number;
  total_duplicates: number;
  chain_details?: ChainSyncDetail[];
  error_message?: string | null;
}

export interface NotificationListResponse {
  success: boolean;
  total: number;
  unread_count: number;
  items: SyncNotificationItem[];
}
