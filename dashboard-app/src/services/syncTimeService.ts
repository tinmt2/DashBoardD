// syncTimeService.ts
// Manages actual data synchronization / import timestamps per chain

const STORAGE_KEYS = {
  'FPT Shop': 'last_sync_fpt_shop',
  'Long Châu': 'last_sync_long_chau',
  'Vaccine': 'last_sync_vaccine',
  'overview': 'last_sync_overview'
} as const;

type ChainKey = 'FPT Shop' | 'Long Châu' | 'Vaccine' | 'overview';

export const getSyncTime = (chain: string = 'overview'): Date | null => {
  try {
    const key = STORAGE_KEYS[chain as ChainKey] || `last_sync_${chain.toLowerCase().replace(/\s+/g, '_')}`;
    const raw = localStorage.getItem(key);
    if (raw) {
      const d = new Date(raw);
      if (!isNaN(d.getTime())) return d;
    }

    // If overview has no record yet, find the latest among the 3 chains
    if (chain === 'overview') {
      const times = ['FPT Shop', 'Long Châu', 'Vaccine']
        .map(c => getSyncTime(c))
        .filter((d): d is Date => d !== null);
      if (times.length > 0) {
        return new Date(Math.max(...times.map(t => t.getTime())));
      }
    }

    // Default initialization on first ever run: record once so it stays stable
    const initialTime = new Date();
    localStorage.setItem(key, initialTime.toISOString());
    return initialTime;
  } catch {
    return null;
  }
};

export const recordSyncTime = (chain: 'FPT Shop' | 'Long Châu' | 'Vaccine' | 'overview' | 'all'): Date => {
  const now = new Date();
  try {
    if (chain === 'all') {
      localStorage.setItem(STORAGE_KEYS['FPT Shop'], now.toISOString());
      localStorage.setItem(STORAGE_KEYS['Long Châu'], now.toISOString());
      localStorage.setItem(STORAGE_KEYS['Vaccine'], now.toISOString());
      localStorage.setItem(STORAGE_KEYS['overview'], now.toISOString());
    } else {
      const key = STORAGE_KEYS[chain];
      if (key) {
        localStorage.setItem(key, now.toISOString());
      }
      // Also update overview if a chain was synced
      localStorage.setItem(STORAGE_KEYS['overview'], now.toISOString());
    }
  } catch (e) {
    console.warn('Failed to save sync time to localStorage', e);
  }
  return now;
};

export const formatSyncTime = (date: Date | null): string => {
  if (!date || isNaN(date.getTime())) return 'Chưa đồng bộ';
  return `${date.toLocaleTimeString('vi-VN')} ${date.toLocaleDateString('vi-VN')}`;
};
