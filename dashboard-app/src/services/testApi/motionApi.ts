import { testApiClient } from './client';
import type { MotionJobState } from '../../types/testEngine';

export const motionApi = {
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    return testApiClient<{ job_id: string; columns: string[] }>('/api/motion/upload', {
      method: 'POST',
      body: formData,
    });
  },

  analyzeData: async (jobId: string, shopCol: string, warningCol: string) => {
    const formData = new FormData();
    formData.append('shop_col', shopCol);
    formData.append('warning_col', warningCol);

    return testApiClient<{ job_id: string }>(`/api/motion/jobs/${jobId}/analyze`, {
      method: 'POST',
      body: formData,
    });
  },

  getJob: async (jobId: string) => {
    return testApiClient<MotionJobState>(`/api/motion/jobs/${jobId}`, {
      method: 'GET',
    });
  },
};
