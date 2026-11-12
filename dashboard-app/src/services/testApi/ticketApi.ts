import { testApiClient } from './client';
import { getTestApiBaseUrl } from './config';
import type { TicketJobState } from '../../types/testEngine';

export const ticketApi = {
  createJob: async (file: File | null, ticketType: string) => {
    const formData = new FormData();
    if (file) formData.append('file', file);
    formData.append('ticket_type', ticketType);

    return testApiClient<{ job_id: string }>('/api/ticket/jobs', {
      method: 'POST',
      body: formData,
    });
  },

  checkJob: async (file: File | null, ticketType: string) => {
    const formData = new FormData();
    if (file) formData.append('file', file);
    formData.append('ticket_type', ticketType);

    return testApiClient<{ job_id: string }>('/api/ticket/jobs/check-status', {
      method: 'POST',
      body: formData,
    });
  },

  getJob: async (jobId: string) => {
    return testApiClient<TicketJobState>(`/api/ticket/jobs/${jobId}`, {
      method: 'GET',
    });
  },

  cancelJob: async (jobId: string) => {
    return testApiClient<null>(`/api/ticket/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  },

  getTicketData: async (ticketType: string) => {
    return testApiClient<any[]>(`/api/ticket/data?ticket_type=${encodeURIComponent(ticketType)}`, {
      method: 'GET',
    });
  },

  downloadJobFile: async (jobId: string, filename: string) => {
    const response = await fetch(`${getTestApiBaseUrl()}/api/ticket/download/${jobId}`);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Tải file thất bại');
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
  },
};
