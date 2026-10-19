import { 
    CalllogOverviewSummary, 
    ChainCalllogStats, 
    CalllogErrorTypeStats, 
    EmployeeErrorRanking 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || (window.location.protocol === 'file:' ? 'http://127.0.0.1:8000' : (window.location.port === '5174' ? `http://${window.location.hostname}:8000` : window.location.origin));

export interface DashboardSummaryResponse {
    success: boolean;
    overview: CalllogOverviewSummary;
    chainStats: ChainCalllogStats[];
    errorTypeStats: CalllogErrorTypeStats[];
    topEmployees: EmployeeErrorRanking[];
}

export interface ImportPreviewResponse {
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

export interface ImportCommitResponse {
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

export const fetchDashboardSummary = async (fromDate?: string, toDate?: string, signal?: AbortSignal): Promise<DashboardSummaryResponse> => {
    const url = new URL(`${API_BASE_URL}/api/fpt-shop/summary`);
    if (fromDate) url.searchParams.append('from_date', fromDate);
    if (toDate) url.searchParams.append('to_date', toDate);
    const response = await fetch(url.toString(), { signal });
    if (!response.ok) {
        throw new Error('Failed to fetch dashboard summary');
    }
    return response.json();
};

export const previewFptShopImport = async (file: File, signal?: AbortSignal): Promise<ImportPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/fpt-shop/import/preview`, {
        method: 'POST',
        body: formData,
        signal
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to preview import');
    }
    return response.json();
};

export const commitFptShopImport = async (importId: string, signal?: AbortSignal): Promise<ImportCommitResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/fpt-shop/import/commit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ import_id: importId }),
        signal
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to commit import');
    }
    return response.json();
};

export interface AuthStatusResponse {
    authenticated: boolean;
    status: string;
}

export const startFptShopAuth = async (creds?: any, signal?: AbortSignal): Promise<AuthStatusResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/fpt-shop/auth/start`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: creds ? JSON.stringify(creds) : JSON.stringify({username: "", password: ""}),
        signal 
    });
    if (!response.ok) {
        throw new Error('Failed to start FPT Shop auth');
    }
    return response.json();
};

export const getFptShopAuthStatus = async (signal?: AbortSignal): Promise<AuthStatusResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/fpt-shop/auth/status`, { signal });
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
    source: string;
    start_date: string;
    end_date: string;
    file_name: string;
    total_rows: number;
    new_records: number;
    updated_records?: number;
    duplicate_records: number;
    invalid_records: number;
    error_message?: string;
}

export const syncFptShop = async (data: SyncRequest, signal?: AbortSignal): Promise<SyncResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/fpt-shop/sync`, { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data),
        signal 
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to sync FPT Shop data');
    }
    const result: SyncResponse = await response.json();
    if (!result.success) {
        throw new Error(result.error_message || 'Đồng bộ FPT Shop thất bại');
    }
    return result;
};

