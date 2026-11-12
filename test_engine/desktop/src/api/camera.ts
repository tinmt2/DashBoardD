import { apiClient, getApiBaseUrl } from './client';

export interface CameraJobResult {
  MaShop?: string;
  TenShop?: string;
  IP_DauGhi?: string;
  Brand?: string;
  Port?: any;
  ChiTiet?: string;
  IP_Cam_Con?: string;
  Port_Cam_Con?: string;
  TrangThai?: string;
  LastRecordTime?: string;
  GhiChu?: string;
  PhanLoai?: string;
  [key: string]: any;
}

export interface CameraJobState {
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  total: number;
  results: CameraJobResult[];
  error: string | null;
  mode?: string;
  cycle?: number;
  cycle_status?: 'scanning' | 'waiting';
  next_cycle_seconds?: number;
  wait_total_seconds?: number;
  metrics?: {
    total_old_errors: number;
    new_errors: number;
    resolved: number;
    scanned: number;
    recovered_count?: number;
    online?: number;
    offline?: number;
    duration?: number;
  };
  results_dict?: {
    total: any[];
    playback: any[];
    ftel: any[];
    hdd: any[];
  };
  last_sync_time?: string;
  last_sync_status?: string;
  last_sync_message?: string;
}

export const cameraApi = {
  createJob: async (file: File | null, options: { vaccine: boolean; lc: boolean; mode: string; periodic?: boolean; interval_minutes?: number }) => {
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
    
    return apiClient<{ job_id: string }>('/api/camera/jobs', {
      method: 'POST',
      body: formData,
    });
  },
  
  getJob: async (jobId: string) => {
    return apiClient<CameraJobState>(`/api/camera/jobs/${jobId}`, {
      method: 'GET',
    });
  },

  cancelJob: async (jobId: string) => {
    return apiClient<null>(`/api/camera/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  },

  exportJob: async (jobId: string) => {
    // Return blob for download
    const response = await fetch(`${getApiBaseUrl()}/api/camera/jobs/${jobId}/export`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error("Export failed");
    return response.blob();
  },

  getWarehouseStatus: async () => {
    return apiClient<any>('/api/camera/warehouse/status', {
      method: 'GET',
    });
  },

  syncJob: async (jobId: string) => {
    return apiClient<any>(`/api/camera/jobs/${jobId}/sync`, {
      method: 'POST',
      timeout: 300000, // 5 minutes timeout for GSheet sync
    });
  },

  skipWait: async (jobId: string) => {
    return apiClient<any>(`/api/camera/jobs/${jobId}/skip-wait`, {
      method: 'POST',
    });
  }
};
