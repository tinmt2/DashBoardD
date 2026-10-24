/**
 * Date and Time utilities for DashBoardD.
 * Ensures consistent handling of UTC timestamps from SQLite/FastAPI across all clients.
 */

/**
 * Parses an ISO date string as UTC even if the timezone suffix (+00:00 or Z) is omitted by SQLite.
 */
export const parseUtcDate = (dateStr?: string | null): Date => {
  if (!dateStr) return new Date();
  let s = String(dateStr).trim();
  // If the date string has no timezone indicator (no Z, and no +HH:MM / -HH:MM offset),
  // append 'Z' so JavaScript parses it as UTC instead of local browser time.
  if (!s.endsWith('Z') && !/[+-]\d{2}(:\d{2})?$/.test(s)) {
    s = s.includes('T') ? s + 'Z' : s.replace(' ', 'T') + 'Z';
  }
  const d = new Date(s);
  return isNaN(d.getTime()) ? new Date(dateStr) : d;
};

/**
 * Formats a timestamp into a human-readable relative time (e.g., 'Vừa xong', '5 phút trước', '2 giờ trước').
 */
export const formatTimeAgo = (dateStr?: string | null): string => {
  if (!dateStr) return '';
  try {
    const date = parseUtcDate(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);

    // If diffSec is slightly negative due to minor server-client clock drift, treat as 'Vừa xong'
    if (diffSec < 45) return 'Vừa xong';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin} phút trước`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour} giờ trước`;
    const diffDay = Math.floor(diffHour / 24);
    if (diffDay < 7) return `${diffDay} ngày trước`;

    return date.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return String(dateStr);
  }
};

/**
 * Formats a timestamp into full localized date and time in Vietnam locale.
 */
export const formatFullDate = (dateStr?: string | null): string => {
  if (!dateStr) return '';
  try {
    const date = parseUtcDate(dateStr);
    return date.toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch {
    return String(dateStr);
  }
};

/**
 * Formats YYYY-MM-DD to DD/MM/YYYY
 */
export const formatDateShort = (dStr?: string | null): string => {
  if (!dStr) return '';
  try {
    const parts = dStr.split('-');
    if (parts.length === 3) {
      return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dStr;
  } catch {
    return dStr;
  }
};
