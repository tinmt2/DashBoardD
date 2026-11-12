import type { TestApiResponse } from '../../types/testEngine';
import { getTestApiBaseUrl } from './config';
import { getSessionId, generateActionId, testLogger } from './logger';

export interface RequestOptions extends RequestInit {
  timeout?: number;
}

/**
 * Generic HTTP client connecting to Test Engine (FastAPI port 18020)
 * Uses standard fetch with timeout, session header, and error parsing.
 */
export async function testApiClient<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<TestApiResponse<T>> {
  const { timeout = 10000, ...fetchOptions } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const sessionId = await getSessionId();
    const actionId = (options.headers as any)?.['x-action-id'] || generateActionId();

    const headers = new Headers(options.headers || {});
    if (sessionId) headers.set('x-session-id', sessionId);
    headers.set('x-action-id', actionId);

    testLogger.debug('API_REQUEST', `Requesting ${options.method || 'GET'} ${endpoint}`, { action_id: actionId });

    const baseUrl = getTestApiBaseUrl();
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

    const response = await fetch(`${baseUrl}${normalizedEndpoint}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timer);

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
      throw new Error(`HTTP ${response.status} — ${errorMsg}`);
    }

    try {
      const data: TestApiResponse<T> = await response.json();
      return data;
    } catch {
      return {
        success: false,
        status: 'error',
        message: 'Invalid JSON response from server',
      };
    }
  } catch (error: any) {
    clearTimeout(timer);

    if (error.name !== 'AbortError') {
      console.error(`[Test API Client] Error: ${error.message}`);
      testLogger.error('API_ERROR', `Request failed: ${endpoint}`, { error_message: error.message });
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
        ? 'Không thể kết nối đến Test Engine Backend (18020). Vui lòng đảm bảo backend đang chạy.'
        : error.message || 'Lỗi mạng không xác định',
    };
  }
}
