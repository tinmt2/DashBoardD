import { API_BASE_URL } from './apiConfig';

export interface AutoSyncConfig {
  enabled: boolean;
  interval_minutes: number;
  sync_chains: string[];
  date_range_days: number;
  sync_mode?: 'current_month' | 'specific_month' | 'days';
  specific_month?: string | null;
  last_run_at: string | null;
  next_run_at: string | null;
  last_status: 'SUCCESS' | 'PARTIAL' | 'FAILED' | null;
  last_message: string | null;
  is_running: boolean;
}

export interface UpdateAutoSyncPayload {
  enabled?: boolean;
  interval_minutes?: number;
  sync_chains?: string[];
  date_range_days?: number;
  sync_mode?: 'current_month' | 'specific_month' | 'days';
  specific_month?: string | null;
}

export const getAutoSyncConfig = async (): Promise<AutoSyncConfig> => {
  const response = await fetch(`${API_BASE_URL}/api/auto-sync/config`);
  if (!response.ok) {
    throw new Error('Không thể tải cấu hình tự động đồng bộ');
  }
  const data = await response.json();
  return data.data;
};

export const updateAutoSyncConfig = async (payload: UpdateAutoSyncPayload): Promise<AutoSyncConfig> => {
  const response = await fetch(`${API_BASE_URL}/api/auto-sync/config`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Không thể cập nhật cấu hình tự động đồng bộ');
  }
  const data = await response.json();
  return data.data;
};

export const triggerAutoSyncRunNow = async (): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(`${API_BASE_URL}/api/auto-sync/run-now`, {
    method: 'POST',
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Không thể kích hoạt tiến trình đồng bộ');
  }
  return await response.json();
};
