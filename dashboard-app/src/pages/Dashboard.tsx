import React, { useState, useEffect, useRef } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

import { createPortal } from 'react-dom';

import { ChevronDown, RefreshCw, AlertCircle, UploadCloud, CheckCircle2, X, Activity, Users } from 'lucide-react';

import type { Chain, Employee } from '../types';

import { GlassCard } from '../components/common/GlassCard';

import { EmployeeService } from '../services/employeeService';
import { fetchVaccineSummary, previewVaccineImport, commitVaccineImport, startVaccineAuth, getVaccineAuthStatus, syncVaccine } from '../services/vaccineApi';
import { fetchLongChauSummary, previewLongChauImport, commitLongChauImport, startLongChauAuth, getLongChauAuthStatus, syncLongChau } from '../services/longChauApi';

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




// Global cache to persist auth state across tab switches (unmounts)
let cachedLcAuth: any = null;
let cachedVacAuth: any = null;
let cachedFptAuth: any = null;

const TannaSVG = () => (<svg width="100%" height="100%" viewBox="0 0 32 32" style={{ filter: 'drop-shadow(0px 2px 3px rgba(0,0,0,0.15))', overflow: 'visible' }}><g fill="#ffffff" stroke="#94a3b8" strokeWidth="0.8"><ellipse cx="16" cy="6" rx="3.5" ry="6" /><ellipse cx="16" cy="26" rx="3.5" ry="6" /><ellipse cx="6" cy="16" rx="6" ry="3.5" /><ellipse cx="26" cy="16" rx="6" ry="3.5" /><ellipse cx="9" cy="9" rx="6" ry="3.5" transform="rotate(45 9 9)" /><ellipse cx="23" cy="23" rx="6" ry="3.5" transform="rotate(45 23 23)" /><ellipse cx="9" cy="23" rx="6" ry="3.5" transform="rotate(-45 9 23)" /><ellipse cx="23" cy="9" rx="6" ry="3.5" transform="rotate(-45 23 9)" /></g><circle cx="16" cy="16" r="4.5" fill="#f59e0b" /><circle cx="15" cy="15" r="1.5" fill="#fbbf24" opacity="0.8" /></svg>);

const CloverSVG = () => (<svg width="100%" height="100%" viewBox="0 0 24 24" style={{ filter: 'drop-shadow(0px 2px 3px rgba(0,0,0,0.15))', overflow: 'visible' }}><circle cx="9.5" cy="9.5" r="4" fill="#4ade80" /><circle cx="14.5" cy="9.5" r="4" fill="#4ade80" /><circle cx="9.5" cy="14.5" r="4" fill="#4ade80" /><circle cx="14.5" cy="14.5" r="4" fill="#4ade80" /><rect x="9.5" y="9.5" width="5" height="5" fill="#4ade80" /><path d="M12 15 Q14 21 9 23" stroke="#4ade80" strokeWidth="1.5" fill="none" strokeLinecap="round"/></svg>);

const Dashboard: React.FC<Props> = ({ chain }) => {


  const textColor = '#1d1d1f';

  const subColor = '#86868b';

  const accentColor = '#FF3B30';



  const [data, setData] = useState<any>(null);
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([
    new Date(new Date().setDate(new Date().getDate() - 7)),
    new Date()
  ]);
  const [startDate, endDate] = dateRange;

  const [activeEmployees, setActiveEmployees] = useState<Employee[]>([]);

  const [loading, setLoading] = useState<boolean>(true);

  const particles = Array.from({ length: 8 }).map((_, i) => ({ id: i, left: Math.random() * 100, size: 20 + Math.random() * 30, sway: Math.random() > 0.5 ? 1 : -1, rotHalf: Math.random() * 180, rot: Math.random() * 360, dur: 3 + Math.random() * 2, delay: Math.random() * 2, type: Math.random() > 0.5 ? 'tanna' : 'clover' }));
  const [mounted, setMounted] = useState(false);
  const [showEffects, setShowEffects] = useState(false);

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

  const [isSyncing, setIsSyncing] = useState(false);

  const [vaccineAuth, setVaccineAuth] = useState<AuthStatusResponse | null>(cachedVacAuth);
  const [longChauAuth, setLongChauAuth] = useState<AuthStatusResponse | null>(cachedLcAuth);
  const [fptAuth, setFptAuth] = useState<AuthStatusResponse | null>(cachedFptAuth);
  const [isVacPolling, setIsVacPolling] = useState(false);
    const [isLcPolling, setIsLcPolling] = useState(false);
  const [expandedErrors, setExpandedErrors] = useState<Record<string, boolean>>({});
  const toggleError = (type: string) => setExpandedErrors(prev => ({ ...prev, [type]: !prev[type] }));
  const [isFptPolling, setIsFptPolling] = useState(false);
  const authState = chain === 'Vaccine' ? vaccineAuth : (chain === 'Long Châu' ? longChauAuth : fptAuth);



  useEffect(() => {
    // Initial check on mount for BOTH if not cached
    getVaccineAuthStatus().then(res => { setVaccineAuth(res); cachedVacAuth = res; if (!res.authenticated && res.status !== 'ERROR' && res.status !== 'STOPPED') setIsVacPolling(true); }).catch(console.error);
    getLongChauAuthStatus().then(res => { setLongChauAuth(res); cachedLcAuth = res; if (!res.authenticated && res.status !== 'ERROR' && res.status !== 'STOPPED') setIsLcPolling(true); }).catch(console.error);
    if (!cachedFptAuth) {
      getFptShopAuthStatus().then(res => { setFptAuth(res); cachedFptAuth = res; cachedFptAuth = res; }).catch(console.error);
    }
  }, []);

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



    const handleStartAuth = async () => {
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
  };



  
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
      if (!importId) return;
      if (chain === 'Vaccine') {
          await commitVaccineImport(importId);
      } else if (chain === 'Long Châu') {
        const importId = (importPreview as any)?.importId;
        if (!importId) return;
        await commitLongChauImport(importId);
      } else {
        const filename = importPreview?.filename;
        if (!filename) return;
        await commitFptShopImport(filename);
      }
      setImportPreview(null);
      await fetchData(); // Refresh data
    } catch (err: any) {
      setImportError(err.message || 'Lỗi khi xử lý file Excel');
    } finally {
      setIsCommitting(false);
    }
  };





  const handleSync = async (e?: React.MouseEvent) => {
    if (e) e.preventDefault();

    setIsSyncing(true);

    try {
      if (!startDate) {
          alert('Vui lòng chọn ngày');
          setIsSyncing(false);
          return;
      }
      const effEndDate = endDate || startDate;
      if (chain === 'Vaccine') {
        await syncVaccine({
          start_date: new Date(startDate.getTime() - startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0],
          end_date: new Date(effEndDate.getTime() - effEndDate.getTimezoneOffset() * 60000).toISOString().split('T')[0]
        });
      } else if (chain === 'Long Châu') {
        await syncLongChau({
          start_date: new Date(startDate.getTime() - startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0],
          end_date: new Date(effEndDate.getTime() - effEndDate.getTimezoneOffset() * 60000).toISOString().split('T')[0]
        });
      } else {
        await syncFptShop({
          start_date: new Date(startDate.getTime() - startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0],
          end_date: new Date(effEndDate.getTime() - effEndDate.getTimezoneOffset() * 60000).toISOString().split('T')[0]
        });
      }

      await fetchData();
      setShowEffects(true);
      setTimeout(() => setShowEffects(false), 6000);
    } catch (err: any) {

      setImportError(err.message || 'Lỗi khi xử lý file Excel');

    } finally {

      setIsSyncing(false);

    }

  };



  const fetchData = async () => {
    setLoading(true);
    setError(null);
    // setData(null); // REMOVED TO PREVENT UI BLINK
    const effEndDate = endDate || startDate;
    const syncStartDate = startDate ? new Date(startDate.getTime() - startDate.getTimezoneOffset() * 60000).toISOString().split('T')[0] : undefined;
    const syncEndDate = effEndDate ? new Date(effEndDate.getTime() - effEndDate.getTimezoneOffset() * 60000).toISOString().split('T')[0] : undefined;
    try {
      if (chain === 'Vaccine') {
        const [vacData, employees] = await Promise.all([
          fetchVaccineSummary(syncStartDate, syncEndDate),
          EmployeeService.getEmployees()
        ]);
        setData(vacData.data);
        setActiveEmployees(employees);
      } else if (chain === 'Long Châu') {
        const [lcData, employees] = await Promise.all([
          fetchLongChauSummary(syncStartDate, syncEndDate),
          EmployeeService.getEmployees()
        ]);
        setData(lcData.data);
        setActiveEmployees(employees);
      } else {
        const [summary, employees] = await Promise.all([
          fetchDashboardSummary(syncStartDate, syncEndDate),
          EmployeeService.getEmployees()
        ]);
        setData(summary);
        setActiveEmployees(employees);
      }
    } catch (err: any) {
      setError(err.message || 'Lỗi cập nhật dữ liệu');
    } finally {
      setLoading(false);
    }
  };



  useEffect(() => {
      fetchData();
      
      setImportPreview(null);
      setImportError(null);
      setIsImporting(false);
      setIsCommitting(false);
      
      // Auto refresh every 5 minutes

    const interval = setInterval(fetchData, 5 * 60 * 1000);
      return () => clearInterval(interval);
    }, [chain]);



  
  
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

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
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
      </div>
    );
  };


  let kpiData = { total: 0, checked: 0, rate: '0%', employees: 0, totalEmployees: 0, reminders: 0 };
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
        reminders: data.totalReminders || 0
      };
      errorTypes = (data.errorTypeStats || []).map((e: any) => ({ type: e.errorType, count: e.count, employees: e.employees }));
      topEmployees = (data.employeeErrorRanking || []).map((e: any) => {
          const rawId = String(e.employeeName || '').trim();
          const matched = activeEmployees.find(emp => {
            const empId = String(emp.id || '').trim().toLowerCase();
            const targetId = rawId.toLowerCase();
            return empId === targetId || empId === targetId + '@fpt.com';
          });
          
          return {
            employeeId: rawId,
            name: matched ? matched.name : rawId,
            chain: chain,
            totalErrors: e.errorCount,
            totalChecked: 0,
            statusStats: e.statusStats || {},
            totalReminders: e.totalReminders || 0,
            isMatched: !!matched
          };
        }).filter((e: any) => e.isMatched);
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
          reminders: overview.totalReminders || 0
        };
      chainData = data.chainStats || [];
      errorTypes = data.errorTypeStats || [];
      topEmployees = data.topEmployees || [];
      ticketStatusStats = (data as any).ticketStatusStats || [];
    }
  }

  return (


    <div className="relative flex-1 overflow-x-hidden font-sans flex flex-col min-h-full">
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-[100]">{particles.map((p) => (<div key={p.id} className="absolute opacity-80" style={{ left: p.left + '%', top: '-10%', width: p.size, height: p.size, animation: showEffects ? 'fall ' + p.dur + 's linear forwards ' + p.delay + 's' : 'none', transformOrigin: 'center' }}><div style={{ animation: showEffects ? 'spin ' + (p.dur * 1.5) + 's linear infinite' : 'none' }}>{p.type === 'tanna' ? <TannaSVG /> : <CloverSVG />}</div></div>))}</div>

      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileSelect} 
        className="hidden" 
        accept=".xls,.xlsx" 
      />

      {renderImportModal()}

      {/* Last updated - top right, below settings button */}

      <p className="absolute top-2 right-6 z-20 text-[12px] font-medium pointer-events-none" style={{ color: subColor }}>

        Cập nhật lần cuối: {new Date().toLocaleString('vi-VN')}

      </p>

      <div className="flex-1 overflow-y-auto px-8 lg:px-12 py-10 relative z-10 w-full animate-fade-in space-y-6">

        

        {/* Top Section */}

        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-8 mb-8 w-full">



          {mounted && document.getElementById('topbar-actions') && createPortal(

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 mr-2">
                {authState?.authenticated ? (
                   <span className="flex items-center justify-center w-9 h-9 rounded-[10px] border border-emerald-200 bg-emerald-50 text-emerald-600 shadow-[0_2px_8px_rgba(16,185,129,0.15)]" title="Connected">
                     <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
                   </span>
                ) : authState?.status === 'STARTING' || authState?.status === 'LOGIN_REQUIRED' || authState?.status === 'LOGIN_PAGE' || authState?.status === 'NAVIGATING' ? (
                   <button onClick={handleStartAuth} className="flex items-center justify-center w-9 h-9 rounded-[10px] border border-amber-200 bg-amber-50 text-amber-600 shadow-[0_2px_8px_rgba(245,158,11,0.15)] hover:bg-amber-100 transition-colors cursor-pointer" title="Đang chờ đăng nhập... Click để mở cửa sổ">
                     <RefreshCw size={16} className="animate-spin" />
                   </button>
                ) : authState?.status === 'OTP_REQUIRED' ? (
                   <button onClick={handleStartAuth} className="flex items-center gap-1.5 text-[13px] font-bold text-indigo-600 bg-indigo-50 px-3 py-1.5 rounded-lg border border-indigo-200 hover:bg-indigo-100 transition-colors cursor-pointer" title="Click để mở Chrome nhập OTP">
                       <AlertCircle size={14} /> Nhập OTP (Mở Chrome)
                     </button>
                ) : authState?.status === 'ERROR' ? (
                   <button onClick={handleStartAuth} className="flex items-center justify-center w-9 h-9 rounded-[10px] border border-rose-200 bg-rose-50 text-rose-600 hover:bg-rose-100 transition-all shadow-sm" title="Lỗi đăng nhập (Thử lại)">
                     <AlertCircle size={16} />
                   </button>
                ) : (
                   <button onClick={handleStartAuth} className="flex items-center gap-1.5 px-3 h-9 rounded-[10px] border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-all shadow-sm" title={chain === 'Vaccine' ? 'Đăng nhập Vaccine' : (chain === 'Long Châu' ? 'Đăng nhập Long Châu' : 'Đăng nhập FPT')}>
                       <Users size={16} />
                       <span className="text-[13px] font-bold">{chain === 'Vaccine' ? 'Đăng nhập Vaccine' : (chain === 'Long Châu' ? 'Đăng nhập Long Châu' : 'Đăng nhập FPT')}</span>
                   </button>
                )}
              </div>
              <button onClick={() => fileInputRef.current?.click()} className="w-9 h-9 flex items-center justify-center bg-blue-50 hover:bg-blue-100 hover:shadow-md hover:-translate-y-0.5 text-blue-600 rounded-[10px] transition-all duration-300 border border-blue-200 shadow-sm" title="Import Excel">
                <UploadCloud size={17} strokeWidth={2.5} />
              </button>
              <button type="button" onClick={handleSync} disabled={isSyncing} className="w-9 h-9 flex items-center justify-center bg-indigo-50 hover:bg-indigo-100 hover:shadow-md hover:-translate-y-0.5 text-indigo-700 rounded-[10px] transition-all duration-300 border border-indigo-200 shadow-sm disabled:opacity-50 disabled:hover:translate-y-0" title="Đồng bộ (Sync)">
                 <RefreshCw size={17} strokeWidth={2.5} className={isSyncing ? "animate-spin" : ""} />
              </button>
              <div className="relative ml-1 z-50">
          <DatePicker
            selectsRange={true}
            startDate={startDate}
            endDate={endDate}
            onChange={(update) => setDateRange(update)}
            dateFormat="dd/MM/yyyy"
            className="px-3 h-9 bg-white hover:bg-slate-50 hover:shadow-md text-slate-700 rounded-[10px] text-[13px] font-bold border border-slate-200 shadow-sm w-[210px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 text-center"
            placeholderText="Chọn ngày"
          />
        </div>
            </div>,
            document.getElementById('topbar-actions')!

          )}



          {/* KPIs */}

          {!isDataEmpty && (

             <GlassCard className="flex-1 flex flex-col md:flex-row items-stretch p-4 md:py-2 relative overflow-hidden bg-white/60 divide-y md:divide-y-0 md:divide-x divide-slate-200/60 shadow-[0_2px_12px_rgba(0,0,0,0.03)] w-full m-0">
                <>
                    <div className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative">
                      <div className="flex items-center gap-3 mb-3 relative z-10">
                        <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">{chain === 'Long Châu' || chain === 'Vaccine' ? 'Tổng Ticket' : 'Tổng Callog'}</span>
                      </div>
                      <div className="text-[48px] font-semibold text-slate-700 leading-none tracking-tight relative z-10">{chain === 'Long Châu' || chain?.includes('Long') ? kpiData.checked : kpiData.total}</div>
                    </div>
                    <div className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative">
                      <div className="flex items-center gap-3 mb-3 relative z-10">
                        <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">Đang xử lý</span>
                      </div>
                      <div className="text-[48px] font-semibold text-slate-700 leading-none tracking-tight relative z-10">
                        {ticketStatusStats.find(s => s.status.toLowerCase().includes('đang') || s.status.toLowerCase().includes('xử lý') || s.status.toLowerCase().includes('ang'))?.count || 0}
                      </div>
                    </div>
                    <div className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative">
                      <div className="flex items-center gap-3 mb-3 relative z-10">
                        <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">Hoàn tất</span>
                      </div>
                      <div className="text-[48px] font-semibold text-slate-700 leading-none tracking-tight relative z-10">
                        {ticketStatusStats.find(s => s.status.toLowerCase().includes('hoàn tất') || s.status.toLowerCase().includes('ho') || s.status.toLowerCase().includes('tất'))?.count || 0}
                      </div>
                    </div>
                    {chain !== 'Vaccine' && (
<div className="flex-1 px-2 md:px-8 py-4 md:py-0 flex flex-col justify-center relative">
                      <div className="flex items-center gap-3 mb-3 relative z-10">
                        <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">Nhắc nhở</span>
                      </div>
                      <div className="text-[48px] font-semibold text-slate-700 leading-none tracking-tight relative z-10">
                        {kpiData.reminders}
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

