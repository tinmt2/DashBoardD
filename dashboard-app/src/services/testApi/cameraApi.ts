import { testApiClient } from './client';
import { getTestApiBaseUrl } from './config';
import type { CameraJobState } from '../../types/testEngine';

export const cameraApi = {
  createJob: async (
    file: File | null,
    options: { vaccine: boolean; lc: boolean; mode: string; periodic?: boolean; interval_minutes?: number }
  ) => {
    const formData = new FormData();
    if (file) formData.append('file', file);
    formData.append('vaccine', options.vaccine.toString());
    formData.append('lc', options.lc.toString());
    formData.append('mode', options.mode);
    if (options.periodic !== undefined) {
      formData.append('periodic', options.periodic.toString());
    }
    if (options.interval_minutes !== undefined) {
      formData.append('interval_minutes', options.interval_minutes.toString());
    }

    return testApiClient<{ job_id: string }>('/api/camera/jobs', {
      method: 'POST',
      body: formData,
    });
  },

  getJob: async (jobId: string) => {
    return testApiClient<CameraJobState>(`/api/camera/jobs/${jobId}`, {
      method: 'GET',
    });
  },

  cancelJob: async (jobId: string) => {
    return testApiClient<null>(`/api/camera/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  },

  exportJob: async (jobId: string) => {
    const response = await fetch(`${getTestApiBaseUrl()}/api/camera/jobs/${jobId}/export`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Xuất file thất bại');
    return response.blob();
  },

  getWarehouseStatus: async () => {
    return testApiClient<any>('/api/camera/warehouse/status', {
      method: 'GET',
    });
  },

  syncJob: async (jobId: string) => {
    return testApiClient<any>(`/api/camera/jobs/${jobId}/sync`, {
      method: 'POST',
      timeout: 300000,
    });
  },

  skipWait: async (jobId: string) => {
    return testApiClient<any>(`/api/camera/jobs/${jobId}/skip-wait`, {
      method: 'POST',
    });
  },
};
