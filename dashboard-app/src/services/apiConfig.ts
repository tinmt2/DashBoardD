export function getApiBaseUrl(): string {
  let envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) {
    envUrl = envUrl.trim();
    if (envUrl && !envUrl.startsWith('http://') && !envUrl.startsWith('https://')) {
      envUrl = `https://${envUrl}`;
    }
    return envUrl.replace(/\/+$/, '');
  }
  return window.location.protocol === 'file:' 
    ? 'http://127.0.0.1:8000' 
    : (window.location.port === '5174' 
        ? `http://${window.location.hostname}:8000` 
        : window.location.origin);
}

export const API_BASE_URL = getApiBaseUrl();
