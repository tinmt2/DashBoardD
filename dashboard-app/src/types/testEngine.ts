export interface TestApiResponse<T = any> {
  success: boolean;
  status: string;
  service?: string;
  data?: T;
  message?: string;
}

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

export interface DvrItem {
  index: number;
  ma_shop: string;
  ten_shop: string;
  vung: string;
  ip: string;
  status: string;
  cam_status: string;
  last_record_time: string;
  note: string;
  error_details: string;
}

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

export interface MotionJobState {
  status: 'uploaded' | 'running' | 'completed' | 'failed' | 'cancelled';
  columns: string[];
  results: Array<{ shop: string; warning: number }>;
  error: string | null;
}

export interface TestAppSettings {
  paths: {
    warehouse_file: string;
  };
  gsheet: {
    configured: boolean;
    spreadsheet_id: string;
    target_gid: number;
    cred_file: string;
  };
  check_cam?: {
    periodic_enabled?: boolean;
    periodic_interval_minutes?: number;
    periodic_auto_sync?: boolean;
    recovery_sheet_name?: string;
  };
}
