import { apiClient, getApiBaseUrl } from './client';

export interface TicketLog {
  msg: string;
}

export interface TicketOutputFile {
  available: boolean;
  filename?: string;
}

export interface TicketError {
  code: string;
  message: string;
}

export interface TicketJobState {
  success: boolean;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  job_id: string;
  message?: string;
  progress: number;
  total: number;
  results: any[];
  logs: TicketLog[];
  output_file?: TicketOutputFile;
  error?: TicketError | null;
}

export const ticketApi = {
  createJob: async (file: File | null, ticketType: string) => {
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    }
    formData.append('ticket_type', ticketType);
    
    return apiClient<{ job_id: string }>('/api/ticket/jobs', {
      method: 'POST',
      body: formData,
    });
  },

  checkJob: async (file: File | null, ticketType: string) => {
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    }
    formData.append('ticket_type', ticketType);
    
    return apiClient<{ job_id: string }>('/api/ticket/jobs/check-status', {
      method: 'POST',
      body: formData,
    });
  },
  
  getJob: async (jobId: string) => {
    return apiClient<TicketJobState>(`/api/ticket/jobs/${jobId}`, {
      method: 'GET',
    });
  },

  cancelJob: async (jobId: string) => {
    return apiClient<null>(`/api/ticket/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  },
  getTicketData: async (ticketType: string) => {
    return apiClient<any[]>(`/api/ticket/data?ticket_type=${encodeURIComponent(ticketType)}`, {
      method: 'GET',
    });
  },

  downloadJobFile: async (jobId: string, filename: string) => {
    const response = await fetch(`${getApiBaseUrl()}/api/ticket/download/${jobId}`);
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Download failed');
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
};

