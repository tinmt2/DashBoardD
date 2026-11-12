import { testApiClient } from './client';
import { getTestApiBaseUrl } from './config';
import type { DvrItem } from '../../types/testEngine';

export const ftelDvrApi = {
  getStatus: async () => {
    return testApiClient<{ is_running: boolean; current: number; total: number; shop: string }>('/api/ftel-dvr/status', {
      method: 'GET',
    });
  },

  getData: async (mode?: string) => {
    const url = mode ? `/api/ftel-dvr/data?mode=${encodeURIComponent(mode)}` : '/api/ftel-dvr/data';
    return testApiClient<DvrItem[]>(url, {
      method: 'GET',
    });
  },

  startScan: async (payload: { mode: string; shops: string[]; delay?: number }) => {
    return testApiClient<null>('/api/ftel-dvr/scan/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },

  stopScan: async () => {
    return testApiClient<null>('/api/ftel-dvr/scan/stop', {
      method: 'POST',
    });
  },

  autoLogin: async (ip: string, port?: any) => {
    return testApiClient<null>('/api/ftel-dvr/auto-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip, port }),
    });
  },

  createJob: async (file: File | null, options: { vaccine: boolean; lc: boolean; mode: string }) => {
    const formData = new FormData();
    if (file) formData.append('file', file);
    formData.append('vaccine', options.vaccine.toString());
    formData.append('lc', options.lc.toString());
    formData.append('mode', options.mode);
    return testApiClient<{ job_id: string }>('/api/ftel-dvr/jobs', {
      method: 'POST',
      body: formData,
    });
  },

  getJob: async (jobId: string) => {
    return testApiClient<any>(`/api/ftel-dvr/jobs/${jobId}`, {
      method: 'GET',
    });
  },

  cancelJob: async (jobId: string) => {
    return testApiClient<null>(`/api/ftel-dvr/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  },

  exportJob: async (jobId: string) => {
    const res = await fetch(`${getTestApiBaseUrl()}/api/ftel-dvr/jobs/${jobId}/export`, {
      method: 'POST',
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text);
    }
    return res.blob();
  },
};
