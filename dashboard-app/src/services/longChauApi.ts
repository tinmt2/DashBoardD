import { LongChauDashboardResponse } from '../types/longChauDashboard';

const API_BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

export const fetchLongChauSummary = async (
  fromDate?: string,
  toDate?: string,
  signal?: AbortSignal
): Promise<LongChauDashboardResponse> => {
  const url = new URL(`${API_BASE_URL}/api/long-chau/summary`);
  if (fromDate) url.searchParams.append('from_date', fromDate);
  if (toDate) url.searchParams.append('to_date', toDate);

  const response = await fetch(url.toString(), { signal });
  
  if (!response.ok) {
    throw new Error('Failed to fetch Long Châu dashboard summary');
  }
  
  return response.json();
};

export interface LongChauImportPreviewResponse {
    success: boolean;
    import_id: string;
    filename: string;
    status: string;
    summary: {
        total_rows: number;
        valid_rows: number;
        invalid_rows: number;
    };
    mapping?: any;
    records?: any[];
    errors?: any[];
    error_message?: string;
}

export interface LongChauImportCommitResponse {
    success: boolean;
    import_id: string;
    summary?: {
        total: number;
        new: number;
        duplicate: number;
        updated: number;
        invalid: number;
    };
    error_message?: string;
}

export const previewLongChauImport = async (file: File, signal?: AbortSignal): Promise<LongChauImportPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/long-chau/import/preview`, {
        method: 'POST',
        body: formData,
        signal
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Lỗi khi preview import Long Châu');
    }
    return response.json();
};

export const commitLongChauImport = async (importId: string, signal?: AbortSignal): Promise<LongChauImportCommitResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/long-chau/import/commit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ import_id: importId }),
        signal
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Lỗi khi commit import Long Châu');
    }
    return response.json();
};


export interface AuthStatusResponse {
    authenticated: boolean;
    status: string;
}

export const startLongChauAuth = async (creds?: any, signal?: AbortSignal): Promise<AuthStatusResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/long-chau/auth/start`, { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: creds ? JSON.stringify(creds) : undefined,
        signal 
    });
    if (!response.ok) {
        throw new Error('Failed to start Long Châu auth');
    }
    return response.json();
};

export const getLongChauAuthStatus = async (signal?: AbortSignal): Promise<AuthStatusResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/long-chau/auth/status`, { signal });
    if (!response.ok) {
        throw new Error('Failed to get auth status');
    }
    return response.json();
};

export interface SyncRequest {
    start_date: string;
    end_date: string;
}

export interface SyncResponse {
    success: boolean;
    start_date: string;
    end_date: string;
    total_rows: number;
    new_records: number;
    duplicate_records: number;
    error_message?: string;
}

export const syncLongChau = async (params: SyncRequest, signal?: AbortSignal): Promise<SyncResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/long-chau/sync`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params),
        signal
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Lỗi khi đồng bộ Long Châu API');
    }
    
    return response.json();
};
