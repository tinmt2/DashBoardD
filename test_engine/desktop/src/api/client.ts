import type { ApiResponse } from '../types/api';
import { getSessionId, generateActionId, logger } from '../utils/logger';

/**
 * Resolves the backend API base URL with priority:
 * 1. Build-time Vite env: import.meta.env.VITE_API_BASE_URL
 * 2. Runtime configuration: window.__API_BASE_URL__
 * 3. Fallback local default: http://127.0.0.1:18020
 * Normalizes by trimming any trailing slashes.
 */
export function getApiBaseUrl(): string {
  let url = '';
  if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) {
    url = String(import.meta.env.VITE_API_BASE_URL).trim();
  } else if (typeof window !== 'undefined' && window.__API_BASE_URL__) {
    url = String(window.__API_BASE_URL__).trim();
  } else {
    url = 'http://127.0.0.1:18020';
  }
  return url.replace(/\/+$/, '');
}

export const API_BASE_URL = getApiBaseUrl();

interface RequestOptions extends RequestInit {
  timeout?: number;
}

/**
 * Generic HTTP client using fetch with timeout and standard error handling.
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const { timeout = 10000, ...fetchOptions } = options;
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const sessionId = await getSessionId();
    const actionId = (options.headers as any)?.['x-action-id'] || generateActionId();
    
    const headers = new Headers(options.headers || {});
    if (sessionId) headers.set('x-session-id', sessionId);
    headers.set('x-action-id', actionId);
    
    logger.debug('API_REQUEST', `Requesting ${options.method || 'GET'} ${endpoint}`, { action_id: actionId });

    const baseUrl = getApiBaseUrl();
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const response = await fetch(`${baseUrl}${normalizedEndpoint}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    clearTimeout(id);

    if (!response.ok) {
      let errorMsg = response.statusText;
      try {
        const errorText = await response.text();
        try {
          const errorJson = JSON.parse(errorText);
          errorMsg = errorJson.detail || errorJson.message || errorText;
        } catch {
          errorMsg = errorText || response.statusText;
        }
      } catch {
        // Ignore body read errors
      }
      throw new Error(`HTTP ${response.status} \u2014 ${errorMsg}`);
    }

    try {
      const data: ApiResponse<T> = await response.json();
      return data;
    } catch (parseError) {
      return {
        success: false,
        status: 'error',
        message: 'Invalid JSON response from server',
      };
    }
  } catch (error: any) {
    clearTimeout(id);

    if (error.name !== 'AbortError') {
      console.error(`[API Client] Error: ${error.message}`);
      logger.error('API_ERROR', `Request failed: ${endpoint}`, { error_message: error.message });
    }

    if (error.name === 'AbortError') {
      return {
        success: false,
        status: 'error',
        message: 'Request timed out',
      };
    }

    return {
      success: false,
      status: 'error',
      message: error.message === 'Failed to fetch' 
        ? 'Connection refused or backend unavailable' 
        : error.message || 'Unknown network error',
    };
  }
}
