import { apiClient } from './client';

export interface MotionJobState {
  status: 'uploaded' | 'running' | 'completed' | 'failed' | 'cancelled';
  columns: string[];
  results: Array<{ shop: string; warning: number }>;
  error: string | null;
}

export const motionApi = {
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient<{ job_id: string; columns: string[] }>('/api/motion/upload', {
      method: 'POST',
      body: formData,
    });
  },

  analyzeData: async (jobId: string, shopCol: string, warningCol: string) => {
    const formData = new FormData();
    formData.append('shop_col', shopCol);
    formData.append('warning_col', warningCol);

    return apiClient<{ job_id: string }>(`/api/motion/jobs/${jobId}/analyze`, {
      method: 'POST',
      body: formData,
    });
  },
  
  getJob: async (jobId: string) => {
    return apiClient<MotionJobState>(`/api/motion/jobs/${jobId}`, {
      method: 'GET',
    });
  }
};
