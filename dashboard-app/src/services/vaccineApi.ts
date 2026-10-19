import { VaccineDashboardResponse } from '../types/vaccineDashboard';

import { API_BASE_URL } from './apiConfig';

export const fetchVaccineSummary = async (
  fromDate?: string,
  toDate?: string,
  signal?: AbortSignal
): Promise<VaccineDashboardResponse> => {
  const url = new URL(`${API_BASE_URL}/api/vaccine/summary`);
  if (fromDate) url.searchParams.append('from_date', fromDate);
  if (toDate) url.searchParams.append('to_date', toDate);

  const response = await fetch(url.toString(), { signal });
  
  if (!response.ok) {
    throw new Error('Failed to fetch Vaccine dashboard summary');
  }
  
  return response.json();
};

export interface VaccineImportPreviewResponse {
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

export interface VaccineImportCommitResponse {
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

export const previewVaccineImport = async (file: File, signal?: AbortSignal): Promise<VaccineImportPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/vaccine/import/preview`, {
        method: 'POST',
        body: formData,
        signal
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Lỗi khi preview import Vaccine');
    }
    return response.json();
};

export const commitVaccineImport = async (importId: string, signal?: AbortSignal): Promise<VaccineImportCommitResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/vaccine/import/commit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ import_id: importId }),
        signal
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Lỗi khi commit import Vaccine');
    }
    return response.json();
};


export interface AuthStatusResponse {
    authenticated: boolean;
    status: string;
}

export const startVaccineAuth = async (creds?: any, signal?: AbortSignal): Promise<AuthStatusResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/vaccine/auth/start`, { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: creds ? JSON.stringify(creds) : undefined,
        signal 
    });
    if (!response.ok) {
        throw new Error('Failed to start Vaccine auth');
    }
    return response.json();
};

export const getVaccineAuthStatus = async (signal?: AbortSignal): Promise<AuthStatusResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/vaccine/auth/status`, { signal });
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

export const syncVaccine = async (params: SyncRequest, signal?: AbortSignal): Promise<SyncResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/vaccine/sync`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params),
        signal
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Lỗi khi đồng bộ Vaccine API');
    }
    
    return response.json();
};
