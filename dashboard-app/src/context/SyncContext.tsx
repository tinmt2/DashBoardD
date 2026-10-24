import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { fetchNotifications } from '../services/notificationService';
import { syncFptShop } from '../services/fptShopApi';
import { syncLongChau } from '../services/longChauApi';
import { syncVaccine } from '../services/vaccineApi';
import { recordSyncTime } from '../services/syncTimeService';
import { useNotification } from './NotificationContext';
import { ChainSyncDetail, NotificationStatus } from '../types/notification';
import { clearDashboardDataCache, clearLongChauAuthCache, clearVaccineAuthCache } from '../pages/Dashboard';

export interface SyncToastInfo {
  show: boolean;
  title: string;
  subtitle?: string;
  type: 'success' | 'warning' | 'error';
}

export interface SyncDateOptions {
  startDate?: Date | null;
  endDate?: Date | null;
  filterMode?: 'all' | number | 'custom';
}

interface SyncContextType {
  isSyncing: boolean;
  syncStepText: string;
  syncDuration: number;
  syncType: 'all' | 'FPT Shop' | 'Long Châu' | 'Vaccine' | null;
  syncToast: SyncToastInfo | null;
  syncVersion: number;
  setSyncToast: React.Dispatch<React.SetStateAction<SyncToastInfo | null>>;
  syncAll: (options?: SyncDateOptions) => Promise<void>;
  syncChain: (chain: 'FPT Shop' | 'Long Châu' | 'Vaccine', options?: SyncDateOptions) => Promise<void>;
}

const SyncContext = createContext<SyncContextType | undefined>(undefined);

export const useSync = () => {
  const context = useContext(SyncContext);
  if (!context) {
    throw new Error('useSync must be used within a SyncProvider');
  }
  return context;
};

function computeDateRange(options?: SyncDateOptions): { syncStartDate: string; syncEndDate: string } {
  const { startDate, endDate, filterMode } = options || {};

  if (filterMode === 'custom' && startDate) {
    const effEndDate = endDate || startDate;
    const startStr = new Date(startDate.getTime() - startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    const endStr = new Date(effEndDate.getTime() - effEndDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    return { syncStartDate: startStr, syncEndDate: endStr };
  } else if (typeof filterMode === 'number') {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - filterMode);
    const startStr = new Date(start.getTime() - start.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    const endStr = new Date(end.getTime() - end.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    return { syncStartDate: startStr, syncEndDate: endStr };
  } else {
    // Default / 'all' mode: sync last 30 days
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 30);
    const startStr = new Date(start.getTime() - start.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    const endStr = new Date(end.getTime() - end.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    return { syncStartDate: startStr, syncEndDate: endStr };
  }
}

export const SyncProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { addNotification, refreshNotifications } = useNotification();
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncStepText, setSyncStepText] = useState<string>('');
  const [syncDuration, setSyncDuration] = useState<number>(0);
  const [syncType, setSyncType] = useState<'all' | 'FPT Shop' | 'Long Châu' | 'Vaccine' | null>(null);
  const [syncToast, setSyncToast] = useState<SyncToastInfo | null>(null);
  const [syncVersion, setSyncVersion] = useState<number>(0);

  // Timer đếm giây theo thời gian thực khi đang đồng bộ
  useEffect(() => {
    let timer: any;
    if (isSyncing) {
      setSyncDuration(0);
      timer = setInterval(() => {
        setSyncDuration(prev => prev + 1);
      }, 1000);
    } else {
      setSyncDuration(0);
    }
    return () => clearInterval(timer);
  }, [isSyncing]);

  const syncAll = useCallback(async (options?: SyncDateOptions) => {
    if (isSyncing) return;
    setIsSyncing(true);
    setSyncType('all');
    setSyncToast(null);

    const { syncStartDate, syncEndDate } = computeDateRange(options);

    const results: { 
      chain: string; 
      ok: boolean; 
      new_records: number; 
      total_rows: number; 
      duplicate_records: number; 
      message?: string; 
    }[] = [];

    // 1. FPT Shop
    try {
      setSyncStepText('Đang tải dữ liệu FPT Shop...');
      const fptRes = await syncFptShop({ start_date: syncStartDate, end_date: syncEndDate });
      results.push({ 
        chain: 'FPT Shop', 
        ok: true, 
        new_records: fptRes?.new_records || 0, 
        total_rows: fptRes?.total_rows || 0, 
        duplicate_records: fptRes?.duplicate_records || 0 
      });
    } catch (err: any) {
      console.warn('FPT Shop sync error:', err);
      results.push({ 
        chain: 'FPT Shop', 
        ok: false, 
        new_records: 0, 
        total_rows: 0, 
        duplicate_records: 0, 
        message: err.message || 'Lỗi kết nối' 
      });
    }

    // 2. Long Châu
    try {
      setSyncStepText('Đang tải dữ liệu Long Châu...');
      const lcRes = await syncLongChau({ start_date: syncStartDate, end_date: syncEndDate });
      results.push({ 
        chain: 'Long Châu', 
        ok: true, 
        new_records: lcRes?.new_records || 0, 
        total_rows: lcRes?.total_rows || 0, 
        duplicate_records: lcRes?.duplicate_records || 0 
      });
    } catch (err: any) {
      console.warn('Long Châu sync error:', err);
      clearLongChauAuthCache();
      results.push({ 
        chain: 'Long Châu', 
        ok: false, 
        new_records: 0, 
        total_rows: 0, 
        duplicate_records: 0, 
        message: err.message || 'Lỗi kết nối' 
      });
    }

    // 3. Vaccine
    try {
      setSyncStepText('Đang tải dữ liệu Vaccine...');
      const vacRes = await syncVaccine({ start_date: syncStartDate, end_date: syncEndDate });
      results.push({ 
        chain: 'Vaccine', 
        ok: true, 
        new_records: vacRes?.new_records || 0, 
        total_rows: vacRes?.total_rows || 0, 
        duplicate_records: vacRes?.duplicate_records || 0 
      });
    } catch (err: any) {
      console.warn('Vaccine sync error:', err);
      clearVaccineAuthCache();
      results.push({ 
        chain: 'Vaccine', 
        ok: false, 
        new_records: 0, 
        total_rows: 0, 
        duplicate_records: 0, 
        message: err.message || 'Lỗi kết nối' 
      });
    }

    // 4. Update data & clear tab caches
    setSyncStepText('Đang cập nhật số liệu...');
    clearDashboardDataCache();

    const successes = results.filter(r => r.ok).map(r => r.chain);
    const failures = results.filter(r => !r.ok);

    if (successes.length > 0) {
      successes.forEach(c => recordSyncTime(c as any));
      recordSyncTime('overview');
    }

    const totalNewErrors = results.reduce((acc, r) => acc + (r.new_records || 0), 0);
    const totalScanned = results.reduce((acc, r) => acc + (r.total_rows || 0), 0);
    const totalDuplicates = results.reduce((acc, r) => acc + (r.duplicate_records || 0), 0);

    const notifStatus: NotificationStatus = failures.length === 0 ? 'SUCCESS' : (successes.length > 0 ? 'PARTIAL' : 'FAILED');
    const notifTitle = failures.length === 0 
      ? 'Đồng bộ thành công cả 3 chuỗi' 
      : (successes.length > 0 ? `Đồng bộ một phần (${successes.join(', ')})` : 'Đồng bộ cả 3 chuỗi thất bại');

    const chainDetails: ChainSyncDetail[] = results.map(r => ({
      chain: r.chain,
      status: r.ok ? 'SUCCESS' : 'FAILED',
      new_records: r.new_records || 0,
      total_rows: r.total_rows || 0,
      duplicate_records: r.duplicate_records || 0,
      error_message: r.ok ? null : r.message
    }));

    addNotification({
      title: notifTitle,
      status: notifStatus,
      sync_type: 'SYNC_ALL',
      start_date: syncStartDate,
      end_date: syncEndDate,
      total_new_errors: totalNewErrors,
      total_scanned: totalScanned,
      total_duplicates: totalDuplicates,
      chain_details: chainDetails,
      error_message: failures.length > 0 ? failures.map(f => `${f.chain}: ${f.message}`).join('; ') : undefined
    }).catch(err => console.error('Lỗi khi lưu thông báo đồng bộ:', err));

    const fptNew = results.find(r => r.chain.toLowerCase().includes('fpt'))?.new_records || 0;
    const lcNew = results.find(r => r.chain.toLowerCase().includes('châu') || r.chain.toLowerCase().includes('chau'))?.new_records || 0;
    const vacNew = results.find(r => r.chain.toLowerCase().includes('vaccine'))?.new_records || 0;

    if (failures.length === 0) {
      setSyncToast({
        show: true,
        type: 'success',
        title: 'Đồng bộ thành công cả 3 chuỗi!',
        subtitle: `Cập nhật thêm: +${fptNew} calllog (FShop), +${lcNew} ticket (Long Châu), +${vacNew} ticket (Vaccine).`
      });
    } else if (successes.length > 0) {
      setSyncToast({
        show: true,
        type: 'warning',
        title: `Đã đồng bộ: ${successes.join(', ')}`,
        subtitle: `FShop: +${fptNew} calllog, Long Châu: +${lcNew} ticket, Vaccine: +${vacNew} ticket.`
      });
    } else {
      setSyncToast({
        show: true,
        type: 'error',
        title: 'Đồng bộ thất bại',
        subtitle: failures.map(f => `${f.chain}: ${f.message}`).join('; ')
      });
    }

    setTimeout(() => setSyncToast(null), 6000);
    setSyncVersion(v => v + 1);
    setIsSyncing(false);
    setSyncStepText('');
    setSyncType(null);
  }, [isSyncing, addNotification]);

  const syncChain = useCallback(async (chain: 'FPT Shop' | 'Long Châu' | 'Vaccine', options?: SyncDateOptions) => {
    if (isSyncing) return;
    setIsSyncing(true);
    setSyncType(chain);
    setSyncToast(null);
    setSyncStepText(`Đang tải dữ liệu ${chain}...`);

    const { syncStartDate, syncEndDate } = computeDateRange(options);

    try {
      let syncRes: any;
      if (chain === 'Vaccine') {
        syncRes = await syncVaccine({ start_date: syncStartDate, end_date: syncEndDate });
      } else if (chain === 'Long Châu') {
        syncRes = await syncLongChau({ start_date: syncStartDate, end_date: syncEndDate });
      } else {
        syncRes = await syncFptShop({ start_date: syncStartDate, end_date: syncEndDate });
      }

      recordSyncTime(chain as any);
      clearDashboardDataCache();

      const newErrors = syncRes?.new_records || 0;
      const updatedErrors = syncRes?.updated_records || 0;
      const totalRows = syncRes?.total_rows || 0;
      const dupRows = syncRes?.duplicate_records || 0;
      const unit = chain.toLowerCase().includes('fpt') ? 'calllog' : 'ticket';
      const syncNotifType = chain === 'Vaccine' ? 'VACCINE' : chain === 'Long Châu' ? 'LONG_CHAU' : 'FPT_SHOP';

      addNotification({
        title: `Đồng bộ ${chain} thành công`,
        status: 'SUCCESS',
        sync_type: syncNotifType,
        start_date: syncStartDate,
        end_date: syncEndDate,
        total_new_errors: newErrors,
        total_scanned: totalRows,
        total_duplicates: dupRows,
        chain_details: [{
          chain,
          status: 'SUCCESS',
          new_records: newErrors,
          total_rows: totalRows,
          duplicate_records: dupRows,
          error_message: null
        }]
      }).catch(e => console.error('Lỗi khi lưu thông báo sync:', e));

      let toastSubtitle = `Đã cập nhật thêm +${newErrors} ${unit} vào hệ thống.`;
      if (updatedErrors > 0) {
        toastSubtitle = `+${newErrors} mới, ${updatedErrors} đã cập nhật trạng thái mới.`;
      }

      setSyncToast({
        show: true,
        type: 'success',
        title: `Đồng bộ ${chain} thành công!`,
        subtitle: toastSubtitle
      });
      setTimeout(() => setSyncToast(null), 4500);
      setSyncVersion(v => v + 1);
    } catch (err: any) {
      const errMsg = String(err.message || '');
      if (errMsg.includes('hết hạn') || errMsg.includes('đăng nhập') || errMsg.includes('401') || errMsg.includes('403')) {
        if (chain === 'Vaccine') {
          clearVaccineAuthCache();
        } else if (chain === 'Long Châu') {
          clearLongChauAuthCache();
        }
      }

      const syncNotifType = chain === 'Vaccine' ? 'VACCINE' : chain === 'Long Châu' ? 'LONG_CHAU' : 'FPT_SHOP';
      addNotification({
        title: `Đồng bộ ${chain} thất bại`,
        status: 'FAILED',
        sync_type: syncNotifType,
        total_new_errors: 0,
        total_scanned: 0,
        total_duplicates: 0,
        chain_details: [{
          chain,
          status: 'FAILED',
          new_records: 0,
          total_rows: 0,
          duplicate_records: 0,
          error_message: errMsg || 'Lỗi khi tải dữ liệu'
        }],
        error_message: errMsg || 'Lỗi khi tải dữ liệu'
      }).catch(e => console.error('Lỗi khi lưu thông báo sync thất bại:', e));

      setSyncToast({
        show: true,
        type: 'error',
        title: `Đồng bộ ${chain} thất bại`,
        subtitle: errMsg || 'Lỗi kết nối máy chủ'
      });
      setTimeout(() => setSyncToast(null), 4500);
    } finally {
      setIsSyncing(false);
      setSyncStepText('');
      setSyncType(null);
    }
  }, [isSyncing, addNotification]);

  // ========================================================
  // REAL-TIME AUTO-SYNC UPDATE DETECTOR
  // Checks for background server syncs every 8 seconds.
  // When an AUTO_SYNC notification finishes on the server:
  // 1. Pops up the animated Global Sync Toast
  // 2. Plays a gentle chime sound
  // 3. Automatically triggers syncVersion to refresh dashboard metrics & charts
  // 4. Updates lastSyncTime across all chains in localStorage
  // 5. Refreshes the notification bell badge & list
  // ========================================================
  const lastKnownNotifIdRef = useRef<string | null>(null);
  const isInitialNotifCheckRef = useRef<boolean>(true);

  const checkBackgroundSyncUpdates = useCallback(async () => {
    try {
      const res = await fetchNotifications(5, 0, false);
      if (!res.success || !res.items || res.items.length === 0) return;

      const latest = res.items[0];

      if (isInitialNotifCheckRef.current) {
        lastKnownNotifIdRef.current = latest.id;
        isInitialNotifCheckRef.current = false;
        return;
      }

      if (latest && latest.id !== lastKnownNotifIdRef.current) {
        lastKnownNotifIdRef.current = latest.id;

        // Refresh bell notification count & list
        refreshNotifications();

        // If this notification was generated by the background server daemon or external sync
        if (latest.sync_type === 'AUTO_SYNC' || !isSyncing) {
          // Increment syncVersion so OverviewDashboard and Dashboard auto-refresh with new data
          setSyncVersion(v => v + 1);

          // Update sync timestamps
          recordSyncTime('all');

          const isSuccess = latest.status === 'SUCCESS';
          const isPartial = latest.status === 'PARTIAL';

          // Format informative subtitle
          let detailText = '';
          if (latest.chain_details && latest.chain_details.length > 0) {
            detailText = latest.chain_details
              .map(d => {
                const u = d.chain.toLowerCase().includes('shop') ? 'calllog' : (d.chain.toLowerCase().includes('vaccine') ? 'phiếu' : 'ticket');
                return `${d.chain}: +${d.new_records} ${u}`;
              })
              .join(' • ');
          } else if (latest.total_new_errors > 0) {
            detailText = `+${latest.total_new_errors} bản ghi/lỗi mới được cập nhật vào hệ thống`;
          } else {
            detailText = 'Dữ liệu toàn hệ thống đã được đồng bộ mới nhất';
          }

          const toastTitle = latest.sync_type === 'AUTO_SYNC'
            ? (isSuccess ? 'Tự động đồng bộ máy chủ hoàn tất!' : isPartial ? 'Tự động đồng bộ hoàn tất (một phần)' : 'Tự động đồng bộ máy chủ thất bại')
            : (latest.title || 'Đồng bộ dữ liệu hoàn tất!');

          setSyncToast({
            show: true,
            type: isSuccess ? 'success' : isPartial ? 'warning' : 'error',
            title: toastTitle,
            subtitle: detailText
          });

          // Play a gentle web audio chime
          try {
            const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
            if (AudioCtx) {
              const ctx = new AudioCtx();
              const osc = ctx.createOscillator();
              const gain = ctx.createGain();
              osc.type = 'sine';
              osc.frequency.setValueAtTime(587.33, ctx.currentTime);
              osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12);
              gain.gain.setValueAtTime(0.04, ctx.currentTime);
              gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.35);
              osc.connect(gain);
              gain.connect(ctx.destination);
              osc.start();
              osc.stop(ctx.currentTime + 0.35);
            }
          } catch {}

          // Auto-hide toast after 7s
          setTimeout(() => {
            setSyncToast(null);
          }, 7000);
        }
      }
    } catch {
      // Ignore background transient network hiccups
    }
  }, [isSyncing, refreshNotifications]);

  useEffect(() => {
    checkBackgroundSyncUpdates();
    const interval = setInterval(checkBackgroundSyncUpdates, 8000);

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        checkBackgroundSyncUpdates();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [checkBackgroundSyncUpdates]);

  return (
    <SyncContext.Provider value={{
      isSyncing,
      syncStepText,
      syncDuration,
      syncType,
      syncToast,
      syncVersion,
      setSyncToast,
      syncAll,
      syncChain
    }}>
      {children}
    </SyncContext.Provider>
  );
};
