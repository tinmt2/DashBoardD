import { apiClient, getApiBaseUrl } from './client';

export interface DvrItem {
  index: number;
  ma_shop: string;
  ten_shop: string;
  vung: string;
  ip: string;
  status: string;
  cam_status: string;
  latency: string;
  password?: string;
}

export interface FtelDvrState {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  total: number;
  results: DvrItem[];
  error: string | null;
}

export const ftelDvrApi = {
  getData: async (refresh: boolean = false) => {
    return apiClient<DvrItem[]>(`/api/ftel-dvr/data?refresh=${refresh}`, { method: 'GET' });
  },

  getStatus: async () => {
    return apiClient<FtelDvrState>('/api/ftel-dvr/status', { method: 'GET' });
  },

  startScan: async () => {
    return apiClient<null>('/api/ftel-dvr/scan/start', { method: 'POST' });
  },

  stopScan: async () => {
    return apiClient<null>('/api/ftel-dvr/scan/stop', { method: 'POST' });
  },

  autoLogin: async (ip: string, port: number, password?: string) => {
    return apiClient<null>('/api/ftel-dvr/auto-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip, port, password })
    });
  },

  createJob: async (file: File | null, options: { vaccine: boolean; lc: boolean; mode: string }) => {
    const formData = new FormData();
    if (file) formData.append('file', file);
    formData.append('vaccine', options.vaccine.toString());
    formData.append('lc', options.lc.toString());
    formData.append('mode', options.mode);
    return apiClient<{ job_id: string }>('/api/ftel-dvr/jobs', { method: 'POST', body: formData });
  },
  
  getJob: async (jobId: string) => {
    return apiClient<any>(`/api/ftel-dvr/jobs/${jobId}`, { method: 'GET' });
  },
  
  cancelJob: async (jobId: string) => {
    return apiClient<null>(`/api/ftel-dvr/jobs/${jobId}/cancel`, { method: 'POST' });
  },

  exportJob: async (jobId: string) => {
    const res = await fetch(`${getApiBaseUrl()}/api/ftel-dvr/jobs/${jobId}/export`, {
      method: 'POST',
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text);
    }
    return res.blob();
  },
};
