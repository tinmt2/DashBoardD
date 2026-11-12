import { API_BASE_URL } from './apiConfig';

export interface InsideCreds {
  username: string;
  password?: string;
}

export interface InsideCredsResponse {
  success: boolean;
  username: string;
  password: string;
  has_password: boolean;
}

export async function getInsideCreds(): Promise<InsideCredsResponse> {
  const token = localStorage.getItem('admin_token');
  const res = await fetch(`${API_BASE_URL}/api/inside/creds`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new Error('Failed to fetch inside creds');
  }
  return res.json();
}

export async function saveInsideCreds(creds: InsideCreds): Promise<{ success: boolean; message: string }> {
  const token = localStorage.getItem('admin_token');
  const res = await fetch(`${API_BASE_URL}/api/inside/creds`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(creds),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to save inside credentials');
  }
  return res.json();
}
