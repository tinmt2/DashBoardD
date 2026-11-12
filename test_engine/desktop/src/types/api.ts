export interface ApiResponse<T = any> {
  success: boolean;
  status: string;
  service?: string;
  data?: T;
  message?: string;
}

export interface HealthResponse extends ApiResponse {
  status: 'ok' | 'error';
}
