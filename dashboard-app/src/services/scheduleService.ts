import { API_BASE_URL } from './apiConfig';
import type { MonthlyScheduleLink, SharePointAuthStatus, ScheduleMatrixData } from '../types';

export const ScheduleService = {
  getScheduleLinks: async (month?: string): Promise<MonthlyScheduleLink[] | MonthlyScheduleLink | null> => {
    try {
      const url = month 
        ? `${API_BASE_URL}/api/employees/schedule-links?month=${encodeURIComponent(month)}`
        : `${API_BASE_URL}/api/employees/schedule-links`;
      const res = await fetch(url);
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn("Could not fetch schedule links from server", e);
    }
    return null;
  },

  saveScheduleLink: async (data: {
    month: string;
    sharepointUrl: string;
    title?: string;
    fileName?: string;
    note?: string;
  }): Promise<MonthlyScheduleLink> => {
    const res = await fetch(`${API_BASE_URL}/api/employees/schedule-links`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Lỗi khi lưu liên kết' }));
      throw new Error(err.detail || 'Lỗi khi lưu liên kết');
    }
    return await res.json();
  },

  deleteScheduleLink: async (month: string): Promise<void> => {
    const res = await fetch(`${API_BASE_URL}/api/employees/schedule-links/${encodeURIComponent(month)}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      throw new Error('Lỗi khi xóa liên kết');
    }
  },

  getSharePointAuthStatus: async (): Promise<SharePointAuthStatus> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/sharepoint/auth/status`);
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn("Could not fetch SharePoint auth status", e);
    }
    return { authenticated: false, status: 'STOPPED' };
  },

  startSharePointAuth: async (targetUrl?: string): Promise<SharePointAuthStatus> => {
    const res = await fetch(`${API_BASE_URL}/api/employees/sharepoint/auth/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ targetUrl: targetUrl || '' }),
    });
    if (!res.ok) {
      throw new Error('Không thể khởi động trình duyệt đăng nhập');
    }
    return await res.json();
  },

  stopSharePointAuth: async (): Promise<void> => {
    await fetch(`${API_BASE_URL}/api/employees/sharepoint/auth/stop`, {
      method: 'POST',
    }).catch(() => {});
  },

  logoutSharePointAuth: async (): Promise<void> => {
    await fetch(`${API_BASE_URL}/api/employees/sharepoint/auth/logout`, {
      method: 'POST',
    }).catch(() => {});
  },

  openSharePointUrl: async (url: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/sharepoint/auth/open`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  getShiftMatrix: async (month: string, chain?: string): Promise<ScheduleMatrixData | null> => {
    try {
      const url = chain && chain !== 'All'
        ? `${API_BASE_URL}/api/employees/schedule/matrix?month=${encodeURIComponent(month)}&chain=${encodeURIComponent(chain)}`
        : `${API_BASE_URL}/api/employees/schedule/matrix?month=${encodeURIComponent(month)}`;
      const res = await fetch(url);
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn("Could not fetch shift matrix", e);
    }
    return null;
  },

  importShiftExcel: async (file: File, month: string): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('month', month);

    const res = await fetch(`${API_BASE_URL}/api/employees/schedule/import-excel`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Lỗi khi nạp file Excel' }));
      throw new Error(err.detail || 'Lỗi khi nạp file Excel');
    }
    return await res.json();
  }
};
