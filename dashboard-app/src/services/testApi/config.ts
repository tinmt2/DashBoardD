/**
 * Test Engine API Configuration
 * Resolution Priority:
 * 1. Build-time Vite env: import.meta.env.VITE_TEST_API_URL
 * 2. Runtime injected variable: window.__TEST_API_BASE_URL__
 * 3. Unified Reverse Proxy on DashBoardD Backend (/api/test)
 *    - In Dev Mode (Port 5174): http://${window.location.hostname}:8000/api/test
 *    - In Production Mode (Port 8000): ${window.location.origin}/api/test
 *    - In Node / non-browser: http://127.0.0.1:8000/api/test
 */
export function getTestApiBaseUrl(): string {
  let url = '';
  if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_TEST_API_URL) {
    url = String(import.meta.env.VITE_TEST_API_URL).trim();
    if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
      url = `http://${url}`;
    }
  } else if (typeof window !== 'undefined' && (window as any).__TEST_API_BASE_URL__) {
    url = String((window as any).__TEST_API_BASE_URL__).trim();
  } else {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname || '127.0.0.1';
      url = window.location.port === '5174'
        ? `http://${hostname}:8000/api/test`
        : `${window.location.origin}/api/test`;
    } else {
      url = 'http://127.0.0.1:8000/api/test';
    }
  }
  return url.replace(/\/+$/, '');
}

export const TEST_API_BASE_URL = getTestApiBaseUrl();
