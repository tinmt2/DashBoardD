import { testApiClient } from './client';
import type { TestApiResponse } from '../../types/testEngine';

export const zaloApi = {
  getStatus: async (includeMessages: boolean = true): Promise<TestApiResponse> => {
    return testApiClient(`/api/zalo/status?include_messages=${includeMessages}`, {
      method: 'GET',
    });
  },

  openBrowser: async (headless: boolean = false): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/open-browser', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ headless }),
    });
  },

  closeBrowser: async (): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/close-browser', {
      method: 'POST',
    });
  },

  getConversations: async (): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/conversations', {
      method: 'GET',
    });
  },

  saveFixedGroup: async (groupName: string): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/save-fixed-group', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_name: groupName }),
    });
  },

  selectGroup: async (groupName: string): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/select-group', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_name: groupName }),
    });
  },

  autoConnect: async (): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/auto-connect', {
      method: 'POST',
    });
  },

  startMonitoring: async (groupName: string, batchIntervalMinutes: number = 10): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_name: groupName, batch_interval_minutes: batchIntervalMinutes }),
    });
  },

  stopMonitoring: async (): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/stop', {
      method: 'POST',
    });
  },

  scanHistory: async (groupName: string, scrollCount: number = 5): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/scan-history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_name: groupName, scroll_count: scrollCount }),
    });
  },

  syncNow: async (): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/sync-now', {
      method: 'POST',
    });
  },

  setBatchInterval: async (batchIntervalMinutes: number): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/set-batch-interval', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_interval_minutes: batchIntervalMinutes }),
    });
  },

  updateGeminiKey: async (apiKey: string): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/config-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gemini_api_key: apiKey }),
    });
  },

  clearData: async (clearDb: boolean = true, clearSheet: boolean = true): Promise<TestApiResponse> => {
    return testApiClient('/api/zalo/clear-data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clear_db: clearDb, clear_sheet: clearSheet }),
    });
  },
};
