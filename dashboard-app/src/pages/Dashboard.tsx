import React, { useState, useEffect, useRef, useCallback } from 'react';
import { LucianDateRangePicker } from '../components/common/LucianDateRangePicker';
import { CircularSpinner } from '../components/common/CircularSpinner';
import { useSync } from '../context/SyncContext';

import { createPortal } from 'react-dom';

import { ChevronDown, RefreshCw, AlertCircle, UploadCloud, CheckCircle2, X, Activity, Users, Calendar, Clock } from 'lucide-react';

import type { Chain, Employee } from '../types';

import { GlassCard } from '../components/common/GlassCard';
import { AnimatedNumber } from '../components/common/AnimatedNumber';
import { useSidebar } from '../components/layout/Layout';

import { EmployeeService } from '../services/employeeService';
import { fetchVaccineSummary, previewVaccineImport, commitVaccineImport, startVaccineAuth, getVaccineAuthStatus, syncVaccine } from '../services/vaccineApi';
import { fetchLongChauSummary, previewLongChauImport, commitLongChauImport, startLongChauAuth, getLongChauAuthStatus, syncLongChau } from '../services/longChauApi';
import { getSyncTime, recordSyncTime, formatSyncTime } from '../services/syncTimeService';
import { useNotification } from '../context/NotificationContext';

import { 

  fetchDashboardSummary, 

  DashboardSummaryResponse, 

  previewFptShopImport, 

  commitFptShopImport,

  startFptShopAuth,

  getFptShopAuthStatus,

  AuthStatusResponse,

  ImportPreviewResponse,

  syncFptShop 

} from '../services/fptShopApi';



interface Props {

  chain?: Chain;

}




// Global cache to persist auth and data across tab switches (unmounts)
let cachedLcAuth: any = null;
let cachedVacAuth: any = null;
let cachedFptAuth: any = null;
export const dashboardDataCache: Record<string, any> = {};
export const dashboardLastUpdatedCache: Record<string, Date | null> = {};
export const clearDashboardDataCache = () => {
  Object.keys(dashboardDataCache).forEach(k => delete dashboardDataCache[k]);
  Object.keys(dashboardLastUpdatedCache).forEach(k => delete dashboardLastUpdatedCache[k]);
};
export const clearVaccineAuthCache = () => {
  cachedVacAuth = { authenticated: false, status: 'LOGIN_PAGE' };
};
export const clearLongChauAuthCache = () => {
  cachedLcAuth = { authenticated: false, status: 'LOGIN_PAGE' };
};
let cachedEmployeesList: Employee[] = [];
let hasAutoCheckedFpt = false;

const Dashboard: React.FC<Props> = ({ chain }) => {
  const { isCollapsed } = useSidebar();
  const chainKey = chain || 'FPT Shop';
  const initialData = dashboardDataCache[chainKey] || null;

  const textColor = '#1d1d1f';
  const subColor = '#86868b';
  const accentColor = '#FF3B30';

  const [data, setData] = useState<any>(initialData);
  const [filterMode, setFilterMode] = useState<'all' | number | 'custom'>('custom');
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([
    new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    new Date()
  ]);
  const [startDate, endDate] = dateRange;
  const [showDatePicker, setShowDatePicker] = useState(false);
  const datePickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (datePickerRef.current && !datePickerRef.current.contains(event.target as Node)) {
        setShowDatePicker(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getFormattedDateRange = () => {
    if (filterMode === 'all') return 'Tất cả ngày';
    const format = (d: Date) => `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth()+1).toString().padStart(2, '0')}/${d.getFullYear()}`;
    if (typeof filterMode === 'number') {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - filterMode);
      if (filterMode === 1) return `Hôm nay (${format(end)})`;
      return `${filterMode} ngày (${format(start)} - ${format(end)})`;
    }
    if (filterMode === 'custom' && startDate) {
      if (endDate) {
        return `${format(startDate)} - ${format(endDate)}`;
      }
      return `${format(startDate)}`;
    }
    return 'Tất cả ngày';
  };

  const handleApplyDateRange = (mode: 'all' | number | 'custom', start: Date | null, end: Date | null) => {
    setFilterMode(mode);
    setDateRange([start, end]);
    dashboardDataCache[chainKey] = null;
    setShowDatePicker(false);
  };

  const [activeEmployees, setActiveEmployees] = useState<Employee[]>(cachedEmployeesList);
  const { addNotification } = useNotification();
  const [loading, setLoading] = useState<boolean>(!initialData);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(() => getSyncTime(chainKey));
  const [mounted, setMounted] = useState(false);
  const [syncToast, setSyncToast] = useState<{ show: boolean; title: string; subtitle?: string } | null>(null);

  useEffect(() => setMounted(true), []);

  const [error, setError] = useState<string | null>(null);



  // Import states

  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isImporting, setIsImporting] = useState(false);

  const [importPreview, setImportPreview] = useState<ImportPreviewResponse | null>(null);

  const [importError, setImportError] = useState<string | null>(null);

  const [isCommitting, setIsCommitting] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [fptCreds, setFptCreds] = useState({ username: '', password: '' });

  useEffect(() => {
    const saved = localStorage.getItem('fptCreds');
    if (saved) {
      try { setFptCreds(JSON.parse(saved)); } catch (e) {}
    }
  }, []);

  const saveSettings = () => {
    localStorage.setItem('fptCreds', JSON.stringify(fptCreds));
    setIsSettingsOpen(false);
  };

  const { isSyncing, syncDuration, syncChain, syncVersion } = useSync();

  const [vaccineAuth, setVaccineAuth] = useState<AuthStatusResponse | null>(cachedVacAuth);
  const [longChauAuth, setLongChauAuth] = useState<AuthStatusResponse | null>(cachedLcAuth);
  const [fptAuth, setFptAuth] = useState<AuthStatusResponse | null>(cachedFptAuth);
  const [isVacPolling, setIsVacPolling] = useState(false);
    const [isLcPolling, setIsLcPolling] = useState(false);
  const [expandedErrors, setExpandedErrors] = useState<Record<string, boolean>>({});
  const toggleError = (type: string) => setExpandedErrors(prev => ({ ...prev, [type]: !prev[type] }));
  const [isFptPolling, setIsFptPolling] = useState(false);
  const authState = chain === 'Vaccine' ? vaccineAuth : (chain === 'Long Châu' ? longChauAuth : fptAuth);



  const handleStartAuth = useCallback(async () => {
    try {
      if (chain === 'Vaccine') {
        const s = { authenticated: false, status: 'STARTING' }; setVaccineAuth(s); cachedVacAuth = s;
        let freshCreds = {username: '', password: ''};
        try { const saved = localStorage.getItem('fptCreds'); if (saved) freshCreds = JSON.parse(saved); } catch(e){}
        const res = await startVaccineAuth(freshCreds);
        setVaccineAuth(res); cachedVacAuth = res;
        if (!res.authenticated) setIsVacPolling(true);
      } else if (chain?.includes('Long')) {
        const s = { authenticated: false, status: 'STARTING' }; setLongChauAuth(s); cachedLcAuth = s;
        let freshCreds = {username: '', password: ''};
        try { const saved = localStorage.getItem('fptCreds'); if (saved) freshCreds = JSON.parse(saved); } catch(e){}
        const res = await startLongChauAuth(freshCreds);
        setLongChauAuth(res); cachedLcAuth = res;
        if (!res.authenticated) setIsLcPolling(true);
      } else {
        const s2 = { authenticated: false, status: 'STARTING' }; setFptAuth(s2); cachedFptAuth = s2;
        let freshCreds = {username: '', password: ''};
        try { const saved = localStorage.getItem('fptCreds'); if (saved) freshCreds = JSON.parse(saved); } catch(e){}
        const res = await startFptShopAuth(freshCreds);
        setFptAuth(res); cachedFptAuth = res;
        if (!res.authenticated) setIsFptPolling(true);
      }
    } catch (e) {
      if (chain === 'Vaccine') setVaccineAuth({ authenticated: false, status: 'ERROR' });
      else if (chain?.includes('Long')) setLongChauAuth({ authenticated: false, status: 'ERROR' });
      else setFptAuth({ authenticated: false, status: 'ERROR' });
    }
  }, [chain]);

  useEffect(() => {
    // Only check auth status for the active chain
    if (chain === 'Vaccine') {
      getVaccineAuthStatus().then(res => {
        setVaccineAuth(res);
        cachedVacAuth = res;
        if (res.status === 'STARTING' || res.status === 'OTP_REQUIRED' || res.status === 'LOGIN_PAGE' || res.status === 'NAVIGATING') {
          setIsVacPolling(true);
        }
      }).catch(console.error);
    } else if (chain === 'Long Châu') {
      getLongChauAuthStatus().then(res => {
        setLongChauAuth(res);
        cachedLcAuth = res;
        if (res.status === 'STARTING' || res.status === 'OTP_REQUIRED' || res.status === 'LOGIN_PAGE' || res.status === 'NAVIGATING') {
          setIsLcPolling(true);
        }
      }).catch(console.error);
    } else {
      getFptShopAuthStatus().then(res => {
        setFptAuth(res);
        cachedFptAuth = res;
        if (res.status === 'STARTING' || res.status === 'OTP_REQUIRED' || res.status === 'LOGIN_PAGE' || res.status === 'NAVIGATING') {
          setIsFptPolling(true);
        } else if (!res.authenticated && !hasAutoCheckedFpt) {
          hasAutoCheckedFpt = true;
          handleStartAuth();
        }
      }).catch(console.error);
    }
  }, [chain, handleStartAuth]);

  // Sync state to cache whenever it changes
  useEffect(() => { if (vaccineAuth) cachedVacAuth = vaccineAuth; }, [vaccineAuth]);
  useEffect(() => { if (longChauAuth) cachedLcAuth = longChauAuth; }, [longChauAuth]);
  useEffect(() => { if (fptAuth) cachedFptAuth = fptAuth; }, [fptAuth]);

  useEffect(() => {
    let vacInterval: any;
    if (isVacPolling) {
      vacInterval = setInterval(() => {
        getVaccineAuthStatus().then((res: any) => {
          setVaccineAuth(res); cachedVacAuth = res;
          if (res.authenticated || res.status === 'ERROR') {
            setIsVacPolling(false);
          }
        }).catch(() => setIsVacPolling(false));
      }, 3000);
    }
    return () => clearInterval(vacInterval);
  }, [isVacPolling]);

  useEffect(() => {
    let lcInterval: any;
    if (isLcPolling) {
      lcInterval = setInterval(() => {
        getLongChauAuthStatus().then((res: any) => {
          setLongChauAuth(res); cachedLcAuth = res;
          if (res.authenticated || res.status === 'ERROR') {
            setIsLcPolling(false);
          }
        }).catch(() => setIsLcPolling(false));
      }, 2000);
    }
    return () => clearInterval(lcInterval);
  }, [isLcPolling]);

  useEffect(() => {
    let fptInterval: any;
    if (isFptPolling) {
      fptInterval = setInterval(() => {
        getFptShopAuthStatus().then((res: any) => {
          setFptAuth(res); cachedFptAuth = res;
          if (res.authenticated || res.status === 'ERROR') {
            setIsFptPolling(false);
          }
        }).catch(() => setIsFptPolling(false));
      }, 2000);
    }
    return () => clearInterval(fptInterval);
  }, [isFptPolling]);




  
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    setImportError(null);
    setImportPreview(null);

    try {
      if (chain === 'Vaccine') {
        const preview = await previewVaccineImport(file);
        setImportPreview(preview as any);
      } else if (chain === 'Long Châu') {
        const preview = await previewLongChauImport(file);
        setImportPreview(preview as any);
      } else {
        const preview = await previewFptShopImport(file);
        setImportPreview(preview as any);
      }
    } catch (err: any) {
      setImportError(err.message || 'Lỗi khi xử lý file Excel');
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  
  const handleCommitImport = async () => {
    setIsCommitting(true);
    try {
      const importId = (importPreview as any)?.importId;
      let commitRes: any;
      if (chain === 'Vaccine') {
        if (!importId) return;
        commitRes = await commitVaccineImport(importId);
      } else if (chain === 'Long Châu') {
        if (!importId) return;
        commitRes = await commitLongChauImport(importId);
      } else {
        const filename = importPreview?.filename;
        if (!filename) return;
        commitRes = await commitFptShopImport(filename);
      }
      setImportPreview(null);
      const syncTime = recordSyncTime((chain || 'FPT Shop') as any);
      setLastSyncTime(syncTime);
      await fetchData(); // Refresh data

      const newErrors = commitRes?.summary?.new ?? commitRes?.new_records ?? 0;
      const totalRows = commitRes?.summary?.total ?? commitRes?.total_rows ?? 0;
      const dupRows = commitRes?.summary?.duplicate ?? commitRes?.duplicate_records ?? 0;

      addNotification({
        title: `Nhập file Excel ${chain || 'FPT Shop'} hoàn tất`,
        status: 'SUCCESS',
        sync_type: 'IMPORT_EXCEL',
        total_new_errors: newErrors,
        total_scanned: totalRows,
        total_duplicates: dupRows,
        chain_details: [
          {
            chain: chain || 'FPT Shop',
            status: 'SUCCESS',
            new_records: newErrors,
            total_rows: totalRows,
            duplicate_records: dupRows,
            error_message: null
          }
        ]
      }).catch(e => console.error('Lỗi khi lưu thông báo import:', e));
    } catch (err: any) {
      setImportError(err.message || 'Lỗi khi xử lý file Excel');
    } finally {
      setIsCommitting(false);
    }
  };

  const handleSync = async (e?: React.MouseEvent) => {
    if (e) e.preventDefault();
    await syncChain(chain || 'FPT Shop', { startDate, endDate, filterMode });
  };

  useEffect(() => {
    if (syncVersion > 0) {
      fetchData();
      setLastSyncTime(getSyncTime((chain || 'FPT Shop') as any));
    }
  }, [syncVersion, chain]);

  const fetchData = async () => {
    // Only set loading to true if we don't already have cached data for this chain
    if (!dashboardDataCache[chainKey]) {
      setLoading(true);
    }
    setError(null);
    let syncStartDate: string | undefined = undefined;
    let syncEndDate: string | undefined = undefined;

    if (filterMode === 'all') {
      syncStartDate = undefined;
      syncEndDate = undefined;
    } else if (typeof filterMode === 'number') {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - filterMode);
      syncStartDate = new Date(start.getTime() - start.getTimezoneOffset() * 60000).toISOString().split('T')[0];
      syncEndDate = new Date(end.getTime() - end.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    } else if (filterMode === 'custom' && startDate) {
      const effEndDate = endDate || startDate;
      syncStartDate = new Date(startDate.getTime() - startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];
      syncEndDate = new Date(effEndDate.getTime() - effEndDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];
    }

    try {
      if (chain === 'Vaccine') {
        const [vacData, employees] = await Promise.all([
          fetchVaccineSummary(syncStartDate, syncEndDate),
          EmployeeService.getEmployees()
        ]);
        dashboardDataCache[chainKey] = vacData.data;
        cachedEmployeesList = employees;
        setData(vacData.data);
        setActiveEmployees(employees);
      } else if (chain === 'Long Châu') {
        const [lcData, employees] = await Promise.all([
          fetchLongChauSummary(syncStartDate, syncEndDate),
          EmployeeService.getEmployees()
        ]);
        dashboardDataCache[chainKey] = lcData.data;
        cachedEmployeesList = employees;
        setData(lcData.data);
        setActiveEmployees(employees);
      } else {
        const [summary, employees] = await Promise.all([
          fetchDashboardSummary(syncStartDate, syncEndDate),
          EmployeeService.getEmployees()
        ]);
        dashboardDataCache[chainKey] = summary;
        cachedEmployeesList = employees;
        setData(summary);
        setActiveEmployees(employees);
      }
      const now = recordSyncTime(chainKey as any);
      setLastSyncTime(now);
    } catch (err: any) {
      setError(err.message || 'Lỗi cập nhật dữ liệu');
    } finally {
      setLoading(false);
    }
  };



  useEffect(() => {
    setLastSyncTime(getSyncTime(chainKey));
    fetchData();
    
    setImportPreview(null);
    setImportError(null);
    setIsImporting(false);
    setIsCommitting(false);
    
    // Auto refresh every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [chain, filterMode, startDate, endDate]);



  
  
  const renderImportModal = () => {
    if (!importPreview && !importError && !isImporting) return null;
    
    // Normalize data for both chains
    const isLongChau = chain === 'Long Châu';
    const isVaccine = chain === 'Vaccine';
    
    let filename = '';
    let totalRows = 0;
    let validRows = 0;
    let invalidRows = 0;
    let canCommit = false;
    
    if (importPreview) {
      if (isLongChau || isVaccine) {
        filename = (importPreview as any).fileName || (importPreview as any).filename;
        totalRows = (importPreview as any).totalRows || 0;
        validRows = (importPreview as any).validRows || 0;
        invalidRows = (importPreview as any).errorRows || 0;
        canCommit = validRows > 0;
      } else {
        filename = importPreview.filename;
        totalRows = importPreview.summary?.total_rows || 0;
        validRows = importPreview.summary?.valid_rows || 0;
        invalidRows = importPreview.summary?.invalid_rows || 0;
        canCommit = validRows > 0;
      }
    }

    return createPortal(
      <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
        <GlassCard className="w-full max-w-lg p-6 flex flex-col relative bg-white">
          <button onClick={() => { setImportPreview(null); setImportError(null); }} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors">
            <X size={20} />
          </button>
          
          <h2 className="text-[18px] font-bold mb-4 text-slate-800">
            {isVaccine ? 'Import dữ liệu Vaccine' : (isLongChau ? 'Import dữ liệu Long Châu' : 'Import dữ liệu FPT Shop')}
          </h2>

          {isImporting ? (
            <div className="flex flex-col items-center justify-center py-8">
              <RefreshCw size={32} className="animate-spin text-blue-500 mb-4" />
              <p className="text-[14px] text-slate-500 font-medium">Đang xử lý...</p>
            </div>
          ) : importError ? (
            <div className="flex flex-col items-center justify-center py-6 text-center">
              <div className="w-12 h-12 rounded-full bg-rose-50 flex items-center justify-center text-rose-500 mb-3">
                <AlertCircle size={24} />
              </div>
              <p className="text-[14px] text-rose-600 font-medium">{importError}</p>
            </div>
          ) : importPreview ? (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-2">
                <div className="flex justify-between items-center pb-2 border-b border-slate-200">
                  <span className="text-[13px] font-medium text-slate-500">File</span>
                  <span className="text-[14px] font-bold text-slate-700">{filename}</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-[13px] font-medium text-slate-500">Tổng số dòng</span>
                  <span className="text-[14px] font-bold text-blue-600">{totalRows}</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-[13px] font-medium text-slate-500">Dòng hợp lệ</span>
                  <span className="text-[14px] font-bold text-emerald-600">{validRows}</span>
                </div>
                {invalidRows > 0 && (
                  <div className="flex justify-between items-center py-1">
                    <span className="text-[13px] font-medium text-slate-500">Dòng lỗi</span>
                    <span className="text-[14px] font-bold text-rose-600">{invalidRows}</span>
                  </div>
                )}
              </div>
              
              <div className="flex justify-end gap-3 mt-6">
                <button 
                  onClick={() => setImportPreview(null)}
                  className="px-4 py-2 rounded-lg text-[13px] font-bold text-slate-600 hover:bg-slate-100 transition-colors"
                >
                  Hủy
                </button>
                <button 
                  onClick={handleCommitImport}
                  disabled={isCommitting || !canCommit}
                  className="px-5 py-2 rounded-lg text-[13px] font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
                >
                  {isCommitting ? (
                    <><RefreshCw size={14} className="animate-spin" /> Đang lưu...</>
                  ) : (
                    <><CheckCircle2 size={16} /> Xác nhận Import</>
                  )}
                </button>
              </div>
            </div>
          ) : null}
        </GlassCard>
      </div>,
      document.body
    );
  };


  let kpiData = { total: 0, checked: 0, rate: '0%', employees: 0, totalEmployees: 0, reminders: 0, nonPenalty: 0, penalty: 0 };
  let chainData: any[] = [];
  let errorTypes: any[] = [];
  let topEmployees: any[] = [];
  let ticketStatusStats: any[] = [];
  let shopErrorRanking: any[] = [];
  let regionErrorStats: any[] = [];

  // fix isDataEmpty for Long Châuse there is no 'overview'
  const isDataEmpty = !data || (data.overview ? data.overview.totalChecked === 0 : data.totalChecked === 0);

  if (!isDataEmpty && data) {
      if (chain === 'Long Châu' || chain === 'Vaccine') {
      kpiData = {
        total: data.totalErrors || 0,
        checked: data.totalChecked || 0,
        rate: `${data.errorRate || 0}%`,
        employees: data.employeesWithErrors || 0,
        totalEmployees: data.totalEmployees || 0,
        reminders: data.totalReminders || 0,
        nonPenalty: data.nonPenaltyCount || 0,
        penalty: data.penaltyCount || 0
      };
      errorTypes = (data.errorTypeStats || []).map((e: any) => ({ type: e.errorType, count: e.count, employees: e.employees }));
      const empMap = new Map<string, any>();
      for (const e of (data.employeeErrorRanking || [])) {
        const rawId = String(e.employeeName || '').trim();
        const matched = activeEmployees.find(emp => {
          const empId = String(emp.id || '').trim().toLowerCase();
          const targetId = rawId.toLowerCase();
          return empId === targetId || empId === targetId + '@fpt.com';
        });

        const key = rawId.toLowerCase();
        if (!empMap.has(key)) {
          empMap.set(key, {
            employeeId: matched ? matched.id : rawId,
            name: matched ? matched.name : rawId,
            chain: chain,
            totalErrors: Number(e.errorCount || 0),
            totalChecked: 0,
            statusStats: { ...(e.statusStats || {}) },
            totalReminders: Number(e.totalReminders || 0),
            isMatched: !!matched
          });
        } else {
          const existing = empMap.get(key);
          existing.totalErrors += Number(e.errorCount || 0);
          existing.totalReminders += Number(e.totalReminders || 0);
          if (e.statusStats) {
            for (const [st, cnt] of Object.entries(e.statusStats)) {
              existing.statusStats[st] = (existing.statusStats[st] || 0) + Number(cnt || 0);
            }
          }
        }
      }
      topEmployees = Array.from(empMap.values())
        .filter((e: any) => e.isMatched)
        .sort((a: any, b: any) => b.totalErrors - a.totalErrors);
      shopErrorRanking = data.shopErrorRanking || [];
      regionErrorStats = data.regionErrorStats || [];
      ticketStatusStats = data.ticketStatusStats || [];
    } else {
      const overview = data.overview || {};
        kpiData = {
          total: overview.totalErrors || 0,
          checked: overview.totalChecked || 0,
          rate: `${overview.errorRate || 0}%`,
          employees: overview.employeesWithErrors || 0,
          totalEmployees: overview.totalEmployees || 0,
          reminders: overview.totalReminders || 0,
          nonPenalty: 0,
          penalty: 0
        };
      chainData = data.chainStats || [];
      errorTypes = data.errorTypeStats || [];
      topEmployees = data.topEmployees || [];
      ticketStatusStats = (data as any).ticketStatusStats || [];
    }
  }

  return (


    <div className="relative flex-1 overflow-x-hidden font-sans flex flex-col min-h-full">

      {/* Sync Success Toast Notification (Mẫu 1 Smooth Glide) */}
      {syncToast?.show && createPortal(
        <div className="fixed top-6 right-6 bg-white/95 backdrop-blur-md border border-emerald-200/80 rounded-2xl p-4 shadow-[0_10px_35px_rgba(0,0,0,0.1)] flex items-center gap-3.5 z-[9999] animate-toast-pop">
          <div className="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center text-lg shrink-0 border border-emerald-100 animate-icon-bounce">
            <CheckCircle2 size={22} className="text-emerald-600" />
          </div>
          <div>
            <div className="text-[14px] font-bold text-slate-800">{syncToast.title}</div>
            {syncToast.subtitle && (
              <div className="text-[12px] font-medium text-slate-500 mt-0.5">{syncToast.subtitle}</div>
            )}
          </div>
          <button 
            type="button"
            onClick={() => setSyncToast(null)} 
            className="ml-2 text-slate-400 hover:text-slate-600 p-1 rounded-lg transition-colors cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>,
        document.body
      )}

      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileSelect} 
        className="hidden" 
        accept=".xls,.xlsx" 
      />

      {renderImportModal()}

      {/* Last updated portaled to Sidebar Footer */}
      {mounted && document.getElementById('sidebar-footer-time') && createPortal(
        isCollapsed ? (
          <div 
            className="flex items-center justify-center text-slate-400 select-none w-full py-1 cursor-pointer"
            title={`Cập nhật lần cuối: ${formatSyncTime(lastSyncTime)}`}
          >
            <Clock size={16} className="text-slate-400" />
          </div>
        ) : (
          <div className="flex items-center gap-2 text-slate-400 select-none w-full">
            <Clock size={13} className="text-slate-400 shrink-0" />
            <div className="flex flex-col leading-tight">
              <span className="text-[9.5px] uppercase tracking-wider font-semibold text-slate-400">Cập nhật lần cuối</span>
              <span className="font-bold text-slate-600 text-[11px] mt-0.5">
                {formatSyncTime(lastSyncTime)}
              </span>
            </div>
          </div>
        ),
        document.getElementById('sidebar-footer-time')!
      )}

      <div className="flex-1 overflow-y-auto px-8 lg:px-12 py-10 relative z-10 w-full animate-fade-in space-y-6">

        {/* Top Section */}
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-8 mb-8 w-full">

          {/* Connect, Import, Sync & DatePicker buttons portaled to Sidebar Header */}
          {mounted && document.getElementById('sidebar-actions') && createPortal(
            isCollapsed ? (
              <div className="flex flex-col items-center gap-2 bg-slate-50/70 rounded-2xl p-1.5 border border-slate-200/60 shadow-2xs w-full">
                {/* 1. Nút Chọn ngày */}
                <div className="relative flex justify-center w-full" ref={datePickerRef}>
                  <button
                    type="button"
                    onClick={() => setShowDatePicker(!showDatePicker)}
                    className="w-10 h-10 rounded-xl flex items-center justify-center bg-white hover:bg-slate-50 text-indigo-600 border border-slate-200/80 transition-all cursor-pointer shadow-2xs"
                    title={`Khoảng ngày: ${getFormattedDateRange()}`}
                  >
                    <Calendar size={16} />
                  </button>
                  {showDatePicker && (
                    <LucianDateRangePicker
                      filterMode={filterMode}
                      startDate={startDate}
                      endDate={endDate}
                      onApply={handleApplyDateRange}
                      onClose={() => setShowDatePicker(false)}
                      positionClasses="absolute left-[calc(100%+14px)] top-0"
                    />
                  )}
                </div>

                {/* 2. Nút Đồng bộ */}
                <button 
                  type="button" 
                  onClick={handleSync} 
                  disabled={isSyncing} 
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all shadow-2xs disabled:opacity-75 cursor-pointer active:scale-95 ${
                    isSyncing 
                      ? "bg-slate-900 text-white border border-slate-800 ring-2 ring-emerald-500/20" 
                      : "bg-white hover:bg-slate-50 text-slate-700 border border-slate-200/80"
                  }`}
                  title={isSyncing ? `Đang tải dữ liệu ${chain || ''}... (${syncDuration}s)` : "Đồng bộ dữ liệu (Sync)"}
                >
                   {isSyncing ? (
                     <CircularSpinner size={16} className="text-emerald-400" />
                   ) : (
                     <RefreshCw size={15} strokeWidth={2.2} />
                   )}
                </button>
              </div>
            ) : (
              <div className="bg-slate-50/70 rounded-2xl p-2 border border-slate-200/60 shadow-[0_2px_8px_rgba(15,23,42,0.03)] flex flex-col gap-2 w-full">
                {/* Row 1: Chọn khoảng ngày */}
                <div className="relative" ref={datePickerRef}>
                  <button 
                    type="button"
                    onClick={() => setShowDatePicker(!showDatePicker)}
                    className="w-full flex items-center justify-between bg-white hover:bg-slate-50/90 rounded-xl border border-slate-200/80 px-2.5 py-1.5 transition-all group cursor-pointer shadow-2xs"
                  >
                    <div className="flex items-center gap-1.5 min-w-0">
                      <Calendar size={13.5} className="text-indigo-600 shrink-0 group-hover:scale-110 transition-transform" />
                      <span className="text-slate-700 text-[11.5px] font-bold truncate">{getFormattedDateRange()}</span>
                    </div>
                    <ChevronDown size={13} className={`text-slate-400 shrink-0 transition-transform duration-200 ${showDatePicker ? 'rotate-180 text-slate-700' : ''}`} />
                  </button>
                  
                  {showDatePicker && (
                    <LucianDateRangePicker
                      filterMode={filterMode}
                      startDate={startDate}
                      endDate={endDate}
                      onApply={handleApplyDateRange}
                      onClose={() => setShowDatePicker(false)}
                      positionClasses="absolute left-[calc(100%+14px)] -top-2"
                    />
                  )}
                </div>

                {/* Row 2: 3 nút icon chức năng trải đều cân đối */}
                <div className="grid grid-cols-3 gap-1.5">
                  {/* 1. Nút Trạng thái / Đăng nhập */}
                  {authState?.authenticated ? (
                     <button 
                       onClick={handleStartAuth}
                       className="h-8.5 rounded-xl flex items-center justify-center bg-emerald-50/90 hover:bg-emerald-100/90 text-emerald-600 border border-emerald-200/80 transition-all shadow-2xs" 
                       title="Đã kết nối (Click để kiểm tra)"
                     >
                       <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse"></span>
                     </button>
                  ) : authState?.status === 'STARTING' || authState?.status === 'LOGIN_REQUIRED' || authState?.status === 'LOGIN_PAGE' || authState?.status === 'NAVIGATING' ? (
                     <button 
                       onClick={handleStartAuth} 
                       className="h-8.5 rounded-xl flex items-center justify-center bg-amber-50 hover:bg-amber-100 text-amber-600 border border-amber-200/80 transition-all shadow-2xs" 
                       title="Đang chờ đăng nhập... Click để mở cửa sổ"
                     >
                       <RefreshCw size={15} className="animate-spin text-amber-600" />
                     </button>
                  ) : authState?.status === 'OTP_REQUIRED' ? (
                     <button 
                       onClick={handleStartAuth} 
                       className="h-8.5 rounded-xl flex items-center justify-center bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200/80 transition-all animate-bounce shadow-2xs" 
                       title="Cần nhập OTP trên trình duyệt Chrome"
                     >
                       <AlertCircle size={16} className="text-indigo-600" />
                     </button>
                  ) : authState?.status === 'ERROR' ? (
                     <button 
                       onClick={handleStartAuth} 
                       className="h-8.5 rounded-xl flex items-center justify-center bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200/80 transition-all shadow-2xs" 
                       title="Lỗi đăng nhập (Click để thử lại)"
                     >
                       <AlertCircle size={16} className="text-rose-600" />
                     </button>
                  ) : (
                     <button 
                       onClick={handleStartAuth} 
                       className="h-8.5 rounded-xl flex items-center justify-center bg-white hover:bg-slate-100 text-slate-600 border border-slate-200/80 transition-all shadow-2xs" 
                       title={`Đăng nhập ${chain}`}
                     >
                       <Users size={16} className="text-slate-600" />
                     </button>
                  )}

                  {/* 2. Nút Import Excel */}
                  <button 
                    onClick={() => fileInputRef.current?.click()} 
                    className="h-8.5 rounded-xl flex items-center justify-center bg-blue-50/90 hover:bg-blue-100/90 text-blue-600 border border-blue-200/80 transition-all shadow-2xs active:scale-95" 
                    title="Import Excel"
                  >
                    <UploadCloud size={16} strokeWidth={2.3} />
                  </button>

                  {/* 3. Nút Đồng bộ */}
                  <button 
                    type="button" 
                    onClick={handleSync} 
                    disabled={isSyncing} 
                    className={`h-8.5 rounded-xl flex items-center justify-center transition-all shadow-2xs disabled:opacity-80 active:scale-95 cursor-pointer ${
                      isSyncing 
                        ? "bg-slate-900 text-white border border-slate-800 ring-2 ring-emerald-500/20" 
                        : "bg-slate-100 hover:bg-slate-200/80 text-slate-700 border border-slate-200/80"
                    }`}
                    title={isSyncing ? `Đang tải dữ liệu ${chain || ''}... (${syncDuration}s)` : "Đồng bộ dữ liệu (Sync)"}
                  >
                     {isSyncing ? (
                       <div className="flex items-center gap-1">
                         <CircularSpinner size={13} className="shrink-0 text-emerald-400" />
                         <span className="text-[10.5px] font-bold tabular-nums text-emerald-400">{syncDuration}s</span>
                       </div>
                     ) : (
                       <RefreshCw size={15} strokeWidth={2.2} />
                     )}
                  </button>
                </div>
              </div>
            ),
            document.getElementById('sidebar-actions')!
          )}

          {/* KPIs */}

          {!isDataEmpty && (

             <GlassCard className="flex-1 flex flex-col md:flex-row items-stretch p-4 md:py-2 relative overflow-hidden bg-white/60 divide-y md:divide-y-0 md:divide-x divide-slate-200/60 shadow-[0_2px_12px_rgba(0,0,0,0.03)] w-full m-0">
                <>
                    <div className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative">
                      <div className="flex items-center gap-3 mb-3 relative z-10">
                        <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">{chain === 'Long Châu' || chain === 'Vaccine' ? 'Tổng Ticket' : 'Tổng Callog'}</span>
                      </div>
                      <div className="text-[48px] font-semibold text-slate-700 leading-none tracking-tight relative z-10">
                        <AnimatedNumber value={Number(chain === 'Long Châu' || chain?.includes('Long') ? kpiData.checked : kpiData.total) || 0} />
                      </div>
                    </div>
                    {ticketStatusStats.some(s => s.status.toLowerCase().includes('chờ') || s.status.toLowerCase().includes('cho')) && (
                      <div className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative">
                        <div className="flex items-center gap-3 mb-3 relative z-10">
                          <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">Chờ xử lý</span>
                        </div>
                        <div className="text-[48px] font-semibold text-slate-700 leading-none tracking-tight relative z-10">
                          <AnimatedNumber value={Number(ticketStatusStats.find(s => s.status.toLowerCase().includes('chờ') || s.status.toLowerCase().includes('cho'))?.count || 0)} />
                        </div>
                      </div>
                    )}
                    <div className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative">
                      <div className="flex items-center gap-3 mb-3 relative z-10">
                        <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">Đang xử lý</span>
                      </div>
                      <div className="text-[48px] font-semibold text-slate-700 leading-none tracking-tight relative z-10">
                        <AnimatedNumber value={Number(ticketStatusStats.find(s => (s.status.toLowerCase().includes('đang') || s.status.toLowerCase().includes('dang')) && !s.status.toLowerCase().includes('chờ'))?.count || 0)} />
                      </div>
                    </div>
                    <div className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative">
                      <div className="flex items-center gap-3 mb-3 relative z-10">
                        <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">Hoàn tất</span>
                      </div>
                      <div className="text-[48px] font-semibold text-slate-700 leading-none tracking-tight relative z-10">
                        <AnimatedNumber value={Number(ticketStatusStats.find(s => s.status.toLowerCase().includes('hoàn tất') || s.status.toLowerCase().includes('hoan tat'))?.count || 0)} />
                      </div>
                    </div>
                    {chain === 'Vaccine' ? (
                      <div 
                        className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative cursor-default"
                        title={`Tổng kết (Cột Y): ${kpiData.nonPenalty} Không phạt • ${kpiData.penalty} Phạt`}
                      >
                        <div className="flex items-center gap-3 mb-3 relative z-10">
                          <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">Không phạt / Phạt</span>
                        </div>
                        <div className="text-[36px] xl:text-[44px] font-semibold text-slate-700 leading-none tracking-tight relative z-10 flex items-baseline">
                          <span className="text-emerald-600">
                            <AnimatedNumber value={Number(kpiData.nonPenalty || 0)} />
                          </span>
                          <span className="text-slate-300 font-light text-[24px] xl:text-[30px] mx-1.5 select-none">/</span>
                          <span className="text-slate-600">
                            <AnimatedNumber value={Number(kpiData.penalty || 0)} />
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative">
                        <div className="flex items-center gap-3 mb-3 relative z-10">
                          <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">Nhắc nhở</span>
                        </div>
                        <div className="text-[48px] font-semibold text-slate-700 leading-none tracking-tight relative z-10">
                          <AnimatedNumber value={Number(kpiData.reminders || 0)} />
                        </div>
                      </div>
                    )}
                  </>
               </GlassCard>

          )}

        </div>



        {loading && isDataEmpty && !error ? (
          <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
            <RefreshCw size={32} className="animate-spin text-slate-400 mb-4" />
            <p className="text-slate-500">Đang tải dữ liệu...</p>
          </div>
        ) : error ? (
          <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
            <GlassCard className="p-8 flex flex-col items-center max-w-md text-center border-rose-200">
              <AlertCircle size={48} className="text-rose-500 mb-4" />
              <h2 className="text-[18px] font-bold mb-2 text-rose-700">Không thể tải dữ liệu {chain || 'FPT Shop'}</h2>
              <p className="text-[14px] mb-6 text-rose-600/80">{error}</p>
              <button onClick={fetchData} className="px-6 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-[14px] font-semibold transition-colors">
                Thử lại
              </button>
            </GlassCard>
          </div>
        ) : isDataEmpty ? (

          <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">

            <GlassCard className="p-8 flex flex-col items-center max-w-md text-center">

              <h2 className="text-[18px] font-bold mb-2" style={{ color: textColor }}>Chưa có dữ liệu</h2>

              <p className="text-[14px] mb-4" style={{ color: subColor }}>Hệ thống chưa có dữ liệu về Calllog/Ticket {chain || 'FPT Shop'}. Vui lòng import dữ liệu từ Excel.</p>

              

            <div className="flex items-center gap-2 justify-center w-full">
              {authState?.authenticated ? (
                 <span className="flex items-center gap-1.5 text-[13px] font-bold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
                   <div className="w-2 h-2 rounded-full bg-emerald-500"></div> Connected
                 </span>
              ) : authState?.status === 'STARTING' || authState?.status === 'LOGIN_REQUIRED' || authState?.status === 'LOGIN_PAGE' || authState?.status === 'NAVIGATING' ? (
                 <button onClick={handleStartAuth} className="flex items-center gap-1.5 text-[13px] font-bold text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200 hover:bg-amber-100 transition-colors cursor-pointer">
                   <RefreshCw size={14} className="animate-spin" /> Đang chờ đăng nhập...
                 </button>
              ) : authState?.status === 'ERROR' ? (
                 <button onClick={handleStartAuth} className="flex items-center gap-1.5 text-[13px] font-bold text-rose-600 bg-rose-50 px-3 py-1.5 rounded-lg border border-rose-200 hover:bg-rose-100 transition-colors">
                     Lỗi đăng nhập (Thử lại)
                 </button>
              ) : (
                 <button onClick={handleStartAuth} className="flex items-center gap-1.5 text-[13px] font-bold text-slate-700 bg-white px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors shadow-sm"> {chain === 'Vaccine' ? 'Đăng nhập Vaccine' : (chain === 'Long Châu' ? 'Đăng nhập Long Châu' : 'Đăng nhập FPT')} </button>
              )}
            </div>
            <button onClick={() => fileInputRef.current?.click()} className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-[14px] font-semibold flex items-center gap-2 transition-colors">

                <UploadCloud size={16} /> Import File Excel

              </button>

            </GlassCard>

          </div>

        ) : (

          <>

            {/* Main Content Grid */}

            <div className={`grid ${chain ? 'grid-cols-2' : 'grid-cols-3'} gap-6 pb-8 min-h-[400px]`}>

              

              {/* Error by Chain */}

              {!chain && (

              <GlassCard className="col-span-1 p-6 flex flex-col">

                <h3 className="text-[16px] font-bold mb-6" style={{ color: textColor }}>Lỗi theo chuỗi</h3>

                <div className="flex-1 space-y-6">

                  {chainData.map((c, i) => (

                    <div key={i}>

                      <div className="flex justify-between items-end mb-2">

                        <span className="text-[14px] font-bold" style={{ color: textColor }}>{c.chain}</span>

                        <div className="flex gap-3 items-baseline">

                          <span className="text-[14px] font-bold" style={{ color: textColor }}>{c.totalErrors}</span>

                          <span className="text-[12px] font-medium" style={{ color: subColor }}>{c.errorRate}%</span>

                        </div>

                      </div>

                      <div className="h-2 w-full bg-black/5 rounded-full overflow-hidden">

                        <div className="h-full rounded-full bg-blue-500" style={{ width: `${(c.totalErrors / (chainData[0]?.totalErrors || 1)) * 100}%` }} />

                      </div>

                    </div>

                  ))}

                </div>

              </GlassCard>

              )}



              {/* Top Employees */}

              <GlassCard className="col-span-1 p-6 flex flex-col">

                <div className="flex justify-between items-center mb-6">

                  <h3 className="text-[16px] font-bold" style={{ color: textColor }}>Danh sách nhân viên theo chuỗi</h3>

                  <button className="text-[13px] font-bold text-blue-600 hover:underline">{chain === 'Long Châu' || chain === 'Vaccine' ? 'Ticket' : 'Callog'}</button>

                </div>

                <div className="flex-1 space-y-4">

                  {(chain ? topEmployees.filter(e => e.chain === chain) : topEmployees).map((emp, i) => {

                      const isMatched = activeEmployees.some(e => {
                          const eId = String(e.id || '').trim().toLowerCase();
                          const empId = String(emp.employeeId || '').trim().toLowerCase();
                          return eId === empId || eId === empId + '@fpt.com' || e.name === emp.name;
                        });

                      return (

                      <div key={i} className="flex items-center justify-between py-3.5 border-b border-black/5 last:border-0 hover:bg-black/5 px-2 -mx-2 rounded-xl transition-colors cursor-pointer group">

                        <div className="flex items-center gap-4">

                          <div className="w-11 h-11 rounded-full bg-slate-200/60 flex items-center justify-center text-[14px] font-bold text-slate-600 shadow-inner">

                            {(emp.name || emp.employeeId || '?').charAt(0)}

                          </div>

                          <div>

                            <div className="text-[15px] font-bold flex items-center gap-2 mb-1" style={{ color: textColor }}>

                              {emp.name || emp.employeeId || 'Không rõ'} 
                                {!isMatched && <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-sm uppercase tracking-wider font-bold">Unmatched</span>}

                            </div>

                            {!chain && <div className="text-[12px] font-medium mb-1.5" style={{ color: subColor }}>{emp.chain}</div>}

                            

                            {/* Clean Status Breakdown (No Borders) */}

                            <div className="flex gap-4 flex-wrap mt-0.5">

                              {emp.statusStats && Object.entries(emp.statusStats).map(([status, count]) => {

                                let dotColor = "bg-slate-400";

                                if (status.toLowerCase().includes('ang') || status.toLowerCase().includes('lý') || status.toLowerCase().includes('ly')) dotColor = "bg-orange-500";

                                if (status.toLowerCase().includes('ho') || status.toLowerCase().includes('tất') || status.toLowerCase().includes('t?t')) dotColor = "bg-emerald-500";
                                if (/^[0-9]+$/.test(status)) dotColor = "bg-blue-400";

                                return (

                                  <div key={status} className="flex items-center gap-1.5">

                                    

                                    <span className="text-[13px] font-medium text-slate-500">

                                      {/^[0-9]+$/.test(status) ? `Bước ${status}` : status} <span className="font-bold text-slate-700 ml-0.5">{count as number}</span>
                                    </span>


                                  </div>

                                );

                              })}

                              

                              {/* Reminder Tag */}
                              {chain !== 'Vaccine' && emp.totalReminders > 0 && (
                                <div className="flex items-center gap-1.5">
                                  <span className="text-[13px] font-medium text-slate-500">
                                    Nhắc nhở <span className="font-bold text-slate-700 ml-0.5">{emp.totalReminders}</span>
                                  </span>
                                </div>
                              )}

                            </div>

                          </div>

                        </div>

                        <div className="flex items-center justify-center min-w-[40px] pr-2">

                          <div className="text-[20px] font-black text-slate-700 group-hover:text-blue-600 transition-colors">

                            {emp.totalErrors}

                          </div>

                        </div>

                      </div>

                    );})}

                </div>

              </GlassCard>



              {/* Top Error Types */}

              <GlassCard className="col-span-1 p-6 flex flex-col">

                <h3 className="text-[16px] font-bold mb-6" style={{ color: textColor }}>Loại lỗi phổ biến</h3>

                <div className="flex-1 space-y-5">

                                    {errorTypes.map((err, i) => (
                    <div key={i} className="flex flex-col gap-2 cursor-pointer group" onClick={() => toggleError(err.type || err.errorType)}>
                      <div className="flex items-center gap-3">
                        <span className="text-[13px] font-bold w-5 opacity-40 group-hover:opacity-100 transition-opacity" style={{ color: textColor }}>{String(i+1).padStart(2, "0")}</span>
                        <div className="flex-1">
                          <div className="flex justify-between mb-1">
                            <span className="text-[14px] font-bold group-hover:text-blue-600 transition-colors" style={{ color: expandedErrors[err.type || err.errorType] ? '#2563eb' : textColor }}>{err.type || err.errorType}</span>
                            <span className="text-[14px] font-bold" style={{ color: textColor }}>{err.count}</span>
                          </div>
                          <div className="h-1.5 w-full bg-black/5 rounded-full overflow-hidden">
                            <div className="h-full rounded-full bg-blue-500/80" style={{ width: `${(err.count / (errorTypes[0]?.count || 1)) * 100}%` }} />
                          </div>
                        </div>
                      </div>
                      {expandedErrors[err.type || err.errorType] && err.employees && err.employees.length > 0 && (
                        <div className="ml-8 p-3 bg-slate-50/80 rounded-lg border border-slate-100 grid grid-cols-2 gap-x-4 gap-y-2">
                          {err.employees.map((emp: any, j: number) => (
                            <div key={j} className="flex justify-between items-center text-[12px]">
                              <span className="text-slate-600 font-medium truncate pr-2" title={emp.name}>{emp.name}</span>
                              <span className="font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">{emp.count}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}

                </div>

              </GlassCard>

            </div>
          </>
        )}

      </div>

    </div>

  );

};



export default Dashboard;

