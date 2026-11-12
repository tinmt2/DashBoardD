import { apiClient } from './client';
import type { HealthResponse } from '../types/api';

export const healthApi = {
  check: () => apiClient<HealthResponse>('/health', { method: 'GET', timeout: 5000 }),
};
