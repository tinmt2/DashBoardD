import { apiClient } from './client';

export interface AppSettings {
  paths: {
    warehouse_file: string;
  };
  gsheet: {
    configured: boolean;
    spreadsheet_id: string;
    target_gid: number;
    cred_file: string;
  };
  check_cam?: {
    periodic_enabled?: boolean;
    periodic_interval_minutes?: number;
    periodic_auto_sync?: boolean;
    recovery_sheet_name?: string;
  };
}

export const settingsApi = {
  getSettings: async () => {
    return apiClient<AppSettings>('/api/settings', {
      method: 'GET',
    });
  },

  updateSettings: async (settings: Partial<AppSettings>) => {
    return apiClient<null>('/api/settings', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
  }
};
