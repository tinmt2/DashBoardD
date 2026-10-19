import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { fetchDashboardSummary, syncFptShop } from '../services/fptShopApi';
import { fetchLongChauSummary, syncLongChau } from '../services/longChauApi';
import { fetchVaccineSummary, syncVaccine } from '../services/vaccineApi';
import { clearDashboardDataCache, clearVaccineAuthCache, clearLongChauAuthCache } from './Dashboard';
import { EmployeeService } from '../services/employeeService';
import { 
  Calendar, ChevronDown, Box, AlertCircle, RefreshCw, Clock, CheckCircle2, X
} from 'lucide-react';
import { LucianDateRangePicker } from '../components/common/LucianDateRangePicker';
import { CircularSpinner } from '../components/common/CircularSpinner';
import { LucianChainKpiCard, LucianRollingDigits } from '../components/dashboard/LucianChainKpiCard';
import { useSidebar } from '../components/layout/Layout';
import { getSyncTime, recordSyncTime, formatSyncTime } from '../services/syncTimeService';
import { useNotification } from '../context/NotificationContext';
import { useSync } from '../context/SyncContext';
import { ChainSyncDetail, NotificationStatus } from '../types/notification';

// Helper to get default date range: from the 1st of the current month to today
const getDefaultDateRange = (): [Date, Date] => {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  return [firstDay, now];
};

const getSavedDateFilter = (): { mode: 'all' | number | 'custom'; range: [Date | null, Date | null] } => {
  try {
    const savedMode = sessionStorage.getItem('overview_filter_mode');
    const savedStart = sessionStorage.getItem('overview_filter_start');
    const savedEnd = sessionStorage.getItem('overview_filter_end');

    if (savedMode === 'all') {
      return { mode: 'all', range: [null, null] };
    }
    if (savedMode === 'custom' && savedStart && savedEnd) {
      const start = new Date(savedStart);
      const end = new Date(savedEnd);
      if (!isNaN(start.getTime()) && !isNaN(end.getTime())) {
        return { mode: 'custom', range: [start, end] };
      }
    }
    if (savedMode && !isNaN(Number(savedMode))) {
      return { mode: Number(savedMode), range: [null, null] };
    }
  } catch (e) {}
  return { mode: 'custom', range: getDefaultDateRange() };
};

const initialDateFilter = getSavedDateFilter();
let cachedOverviewFilterMode: 'all' | number | 'custom' = initialDateFilter.mode;
let cachedOverviewDateRange: [Date | null, Date | null] = initialDateFilter.range;
export let cachedOverviewData: any = null;

const OverviewDashboard: React.FC = () => {
  const { isCollapsed } = useSidebar();
  const { isSyncing, syncStepText, syncDuration, syncAll, syncVersion } = useSync();
  const [loading, setLoading] = useState(!cachedOverviewData);
  const [data, setData] = useState<any>(cachedOverviewData || { fpt: [], lc: [], vac: [] });
  const [activeEmployees, setActiveEmployees] = useState<any[]>([]);
  const [filterMode, setFilterMode] = useState<'all' | number | 'custom'>(cachedOverviewFilterMode);
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>(cachedOverviewDateRange);
  const [startDate, endDate] = dateRange;
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(() => getSyncTime('overview'));
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [mounted, setMounted] = useState(false);
  const datePickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    EmployeeService.getEmployees().then(setActiveEmployees).catch(() => {});
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (datePickerRef.current && !datePickerRef.current.contains(event.target as Node)) {
        setShowDatePicker(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchData = useCallback(async () => {
    if (!cachedOverviewData) {
      setLoading(true);
    }
    try {
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
      } else if (filterMode === 'custom' && startDate && endDate) {
        syncStartDate = new Date(startDate.getTime() - startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];
        syncEndDate = new Date(endDate.getTime() - endDate.getTimezoneOffset() * 60000).toISOString().split('T')[0];
      }

      const [fpt, lc, vac] = await Promise.all([
        fetchDashboardSummary(syncStartDate, syncEndDate),
        fetchLongChauSummary(syncStartDate, syncEndDate),
        fetchVaccineSummary(syncStartDate, syncEndDate)
      ]);
    
      const newData = {
        fpt: fpt.errorTypeStats || [],
        lc: lc.data?.errorTypeStats || [],
        vac: vac.data?.errorTypeStats || []
      };
      cachedOverviewData = newData;
      setData(newData);
      const now = recordSyncTime('overview');
      setLastSyncTime(now);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [filterMode, startDate, endDate]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000); // 5 minutes
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleSyncAll = () => {
    syncAll({ startDate, endDate, filterMode });
  };

  useEffect(() => {
    if (syncVersion > 0) {
      cachedOverviewData = null;
      fetchData();
      setLastSyncTime(getSyncTime('overview'));
    }
  }, [syncVersion, fetchData]);

  const globalMaxCount = useMemo(() => {
    let max = 0;
    const allErrors = [
      ...(data.fpt || []),
      ...(data.lc || []),
      ...(data.vac || [])
    ];
    for (const err of allErrors) {
      if (err.count > max) max = err.count;
    }
    return max;
  }, [data]);

  const { systemTotal } = useMemo(() => {
    const fpt = (data.fpt || []).reduce((s: number, e: any) => s + (e.count || 0), 0);
    const lc = (data.lc || []).reduce((s: number, e: any) => s + (e.count || 0), 0);
    const vac = (data.vac || []).reduce((s: number, e: any) => s + (e.count || 0), 0);
    return {
      systemTotal: fpt + lc + vac
    };
  }, [data]);

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
    cachedOverviewFilterMode = mode;
    cachedOverviewDateRange = [start, end];
    try {
      sessionStorage.setItem('overview_filter_mode', String(mode));
      if (start) sessionStorage.setItem('overview_filter_start', start.toISOString());
      else sessionStorage.removeItem('overview_filter_start');
      if (end) sessionStorage.setItem('overview_filter_end', end.toISOString());
      else sessionStorage.removeItem('overview_filter_end');
    } catch (e) {}
    cachedOverviewData = null; // Invalidate cached data so fresh data is fetched
    setShowDatePicker(false);
  };

  return (
    <div className="p-8 max-w-[1700px] mx-auto h-full flex flex-col bg-[#f8fbff]/50">
      
      {/* DatePicker & SyncAll button portaled to Sidebar Actions */}
      {mounted && document.getElementById('sidebar-actions') && createPortal(
        isCollapsed ? (
          <div className="flex flex-col items-center gap-2 bg-slate-50/70 rounded-2xl p-1.5 border border-slate-200/60 shadow-2xs w-full">
            {/* Date button icon */}
            <div className="relative w-full flex justify-center" ref={datePickerRef}>
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

            {/* Duy nhất 1 nút Đồng bộ tất cả (icon mode) */}
            <button
              type="button"
              onClick={handleSyncAll}
              disabled={isSyncing || loading}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all cursor-pointer active:scale-95 shadow-2xs ${
                isSyncing 
                  ? "bg-slate-900 text-white border border-slate-800 ring-2 ring-emerald-500/20" 
                  : "bg-slate-900 hover:bg-slate-800 text-white border border-slate-900"
              } disabled:opacity-60`}
              title={isSyncing ? `${syncStepText || "Đang tải dữ liệu..."} (${syncDuration}s)` : "Đồng bộ tất cả 3 chuỗi"}
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

            {/* Row 2: Duy nhất 1 nút Đồng bộ tất cả full width */}
            <button 
              type="button"
              onClick={handleSyncAll}
              disabled={isSyncing || loading}
              className={`w-full h-8.5 rounded-xl flex items-center justify-center gap-1.5 font-bold text-[12px] transition-all cursor-pointer px-3 active:scale-[0.98] shadow-2xs ${
                isSyncing 
                  ? "bg-slate-900 text-white border border-slate-800 ring-2 ring-emerald-500/20" 
                  : "bg-slate-900 hover:bg-slate-800 text-white border border-slate-900"
              } disabled:opacity-60`}
              title="Đồng bộ cả 3 chuỗi (FPT Shop, Long Châu, Vaccine)"
            >
              {isSyncing ? (
                <>
                  <CircularSpinner size={13.5} className="shrink-0 text-emerald-400" />
                  <span className="truncate">{syncStepText || "Đang tải dữ liệu..."}</span>
                  <span className="text-[11px] font-bold text-emerald-400 tabular-nums shrink-0">({syncDuration}s)</span>
                </>
              ) : (
                <>
                  <RefreshCw size={13} strokeWidth={2.2} className="shrink-0" />
                  <span className="truncate">Đồng bộ tất cả</span>
                </>
              )}
            </button>
          </div>
        ),
        document.getElementById('sidebar-actions')!
      )}

      {/* Overview Header & Lucian #098 Summary Badges */}
      <div className="mb-6 flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        <div>
          <h1 className="text-[26px] font-bold text-slate-800 tracking-tight mb-1">
            Tổng quan
          </h1>
          <p className="text-[14px] font-medium text-slate-400">
            Thống kê các loại lỗi theo từng chuỗi hệ thống
          </p>
        </div>

        {/* Lucian #098 Live Summary Strip */}
        <div className="flex items-center">
          <div className="bg-white/95 backdrop-blur-md rounded-2xl px-4 py-2 border border-slate-200/80 shadow-2xs flex items-center">
            <div className="flex flex-col">
              <span className="text-[9.5px] font-bold uppercase tracking-wider text-slate-400">Tổng lỗi 3 chuỗi</span>
              <div className="text-[17px] font-black text-slate-900 leading-tight">
                <LucianRollingDigits value={systemTotal} />
              </div>
            </div>
          </div>
        </div>
      </div>

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

      {/* Main Content Area */}
      {loading && !cachedOverviewData ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-pulse flex flex-col items-center gap-4">
            <div className="w-10 h-10 border-3 border-slate-100 border-t-indigo-500 rounded-full animate-spin"></div>
            <div className="text-slate-400 font-medium text-sm">Đang tải dữ liệu...</div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0 pb-6">
          <LucianChainKpiCard 
            title="FPT SHOP" 
            chainCode="fpt"
            errors={data.fpt} 
            colorTheme="rose"
            route="/fpt-shop"
            globalMaxCount={globalMaxCount}
            totalSystemErrors={systemTotal}
            activeEmployees={activeEmployees}
          />
          <LucianChainKpiCard 
            title="LONG CHÂU" 
            chainCode="lc"
            errors={data.lc} 
            colorTheme="blue"
            route="/long-chau"
            globalMaxCount={globalMaxCount}
            totalSystemErrors={systemTotal}
            activeEmployees={activeEmployees}
          />
          <LucianChainKpiCard 
            title="VACCINE" 
            chainCode="vac"
            errors={data.vac} 
            colorTheme="teal"
            route="/vaccine"
            globalMaxCount={globalMaxCount}
            totalSystemErrors={systemTotal}
            activeEmployees={activeEmployees}
          />
        </div>
      )}

    </div>
  );
};

export default OverviewDashboard;
