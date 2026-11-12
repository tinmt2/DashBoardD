import type { ApiResponse } from '../types/api';
import { getApiBaseUrl } from './client';

export const zaloApi = {
  getStatus: async (includeMessages: boolean = true): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/status?include_messages=${includeMessages}`);
    return res.json();
  },

  openBrowser: async (headless: boolean = false): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/open-browser`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ headless }),
    });
    return res.json();
  },

  closeBrowser: async (): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/close-browser`, {
      method: 'POST',
    });
    return res.json();
  },

  getConversations: async (): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/conversations`);
    return res.json();
  },

  saveFixedGroup: async (groupName: string): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/save-fixed-group`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_name: groupName }),
    });
    return res.json();
  },

  selectGroup: async (groupName: string): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/select-group`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_name: groupName }),
    });
    return res.json();
  },

  autoConnect: async (): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/auto-connect`, {
      method: 'POST',
    });
    return res.json();
  },

  startMonitoring: async (groupName: string, batchIntervalMinutes: number = 10): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_name: groupName, batch_interval_minutes: batchIntervalMinutes }),
    });
    return res.json();
  },

  stopMonitoring: async (): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/stop`, {
      method: 'POST',
    });
    return res.json();
  },

  scanHistory: async (groupName: string, scrollCount: number = 5): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/scan-history`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group_name: groupName, scroll_count: scrollCount }),
    });
    return res.json();
  },

  syncNow: async (): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/sync-now`, {
      method: 'POST',
    });
    return res.json();
  },

  setBatchInterval: async (batchIntervalMinutes: number): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/set-batch-interval`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_interval_minutes: batchIntervalMinutes }),
    });
    return res.json();
  },

  updateGeminiKey: async (apiKey: string): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/config-key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gemini_api_key: apiKey }),
    });
    return res.json();
  },

  clearData: async (clearDb: boolean = true, clearSheet: boolean = true): Promise<ApiResponse> => {
    const res = await fetch(`${getApiBaseUrl()}/api/zalo/clear-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clear_db: clearDb, clear_sheet: clearSheet }),
    });
    return res.json();
  },
};
