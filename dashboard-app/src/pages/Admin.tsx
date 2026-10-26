// Lucian UX/UI Prompt #039 Sliding Pill Tabs · MIT License (c) 2026 Seokwoooo · https://lucianlabs.dev/uxui-prompt/#039
// Streamlined & Clean Admin Dashboard for DashBoardD

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Eye, EyeOff, Loader2
} from 'lucide-react';
import { 
  getAutoSyncConfig, 
  updateAutoSyncConfig, 
  triggerAutoSyncRunNow, 
  AutoSyncConfig 
} from '../services/autoSyncApi';
import { GlassCard } from '../components/common/GlassCard';
import BrandLogo from '../components/common/BrandLogo';
import { parseUtcDate } from '../utils/dateUtils';

interface SystemOverview {
  system: {
    status: string;
    port: number;
    uptime_seconds: number;
    uptime_str: string;
    cpu_percent: number;
    ram_percent: number;
    ram_used_gb: number;
    ram_total_gb: number;
  };
  database: {
    db_size_mb: number;
    total_tickets: number;
    fpt_tickets: number;
    long_chau_tickets: number;
    vaccine_tickets: number;
    notifications_count: number;
  };
  chains: {
    fpt_shop: { status: string; authenticated: boolean };
    long_chau: { status: string; authenticated: boolean };
    vaccine: { status: string; authenticated: boolean };
  };
  recent_notifications: Array<{
    id: string;
    chain: string;
    title: string;
    message: string;
    status: string;
    created_at: string;
  }>;
  recent_jobs: Array<{
    id: string;
    filename: string;
    status: string;
    total_rows: number;
    created_at: string;
  }>;
  checked_at: string;
}

type AdminTab = 'system' | 'autosync' | 'logs' | 'audit';

const Admin: React.FC = () => {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('admin_token'));
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Active Tab state (Lucian #039 Sliding Pill Tabs)
  const [activeTab, setActiveTab] = useState<AdminTab>('system');

  // Overview data
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [isLoadingOverview, setIsLoadingOverview] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Change password modal
  const [isChangePwOpen, setIsChangePwOpen] = useState(false);
  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [pwError, setPwError] = useState('');
  const [pwSuccess, setPwSuccess] = useState('');

  // Log Viewer State
  const [logs, setLogs] = useState<Array<{ id: string; timestamp: string; level: string; logger: string; message: string }>>([]);
  const [logLevelFilter, setLogLevelFilter] = useState<'ALL' | 'ERROR' | 'WARNING' | 'INFO'>('ALL');
  const [logSearch, setLogSearch] = useState('');
  const [logLinesLimit, setLogLinesLimit] = useState(200);
  const [isAutoRefreshLogs, setIsAutoRefreshLogs] = useState(true);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);
  const [autoScrollLogs, setAutoScrollLogs] = useState(true);
  const [isTestingSync, setIsTestingSync] = useState(false);
  const [testSyncResult, setTestSyncResult] = useState<{ success: boolean; message: string } | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Auto-Sync Scheduler State
  const [autoSyncConfig, setAutoSyncConfig] = useState<AutoSyncConfig | null>(null);
  const [autoSyncForm, setAutoSyncForm] = useState<{
    enabled: boolean;
    interval_minutes: number;
    sync_chains: string[];
    date_range_days: number;
  }>({
    enabled: false,
    interval_minutes: 60,
    sync_chains: ['fpt_shop', 'long_chau', 'vaccine'],
    date_range_days: 30,
  });
  const [isSavingAutoSync, setIsSavingAutoSync] = useState(false);
  const [isTriggeringAutoSync, setIsTriggeringAutoSync] = useState(false);
  const [autoSyncFeedback, setAutoSyncFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // 1. Verify token on load
  useEffect(() => {
    if (token) {
      fetch('/api/admin/verify', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => {
          if (!res.ok) {
            setToken(null);
            localStorage.removeItem('admin_token');
          }
        })
        .catch(() => {});
    }
  }, [token]);

  // 2. Fetch Overview
  const fetchOverview = async () => {
    try {
      setIsLoadingOverview(true);
      const res = await fetch('/api/admin/overview');
      if (res.ok) {
        const data = await res.json();
        setOverview(data);
      }
    } catch (err) {
      console.error("Lỗi tải thông tin admin:", err);
    } finally {
      setIsLoadingOverview(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    fetchOverview();

    let interval: ReturnType<typeof setInterval> | null = null;
    if (autoRefresh) {
      interval = setInterval(fetchOverview, 5000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [token, autoRefresh]);

  // Fetch logs
  const fetchLogs = async () => {
    try {
      setIsLoadingLogs(true);
      const params = new URLSearchParams({
        lines: logLinesLimit.toString(),
        level: logLevelFilter,
      });
      if (logSearch.trim()) {
        params.append('search', logSearch.trim());
      }
      const res = await fetch(`/api/admin/logs?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch (err) {
      console.error("Lỗi khi tải log:", err);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    fetchLogs();

    let logInterval: ReturnType<typeof setInterval> | null = null;
    if (isAutoRefreshLogs) {
      logInterval = setInterval(fetchLogs, 2500);
    }
    return () => {
      if (logInterval) clearInterval(logInterval);
    };
  }, [token, isAutoRefreshLogs, logLevelFilter, logLinesLimit, logSearch]);

  // Auto-scroll log box
  useEffect(() => {
    if (autoScrollLogs && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScrollLogs]);

  // Clear logs
  const handleClearLogs = async () => {
    if (!confirm('Bạn có chắc muốn xóa sạch log trên màn hình không?')) return;
    try {
      await fetch('/api/admin/logs', { method: 'DELETE' });
      setLogs([]);
    } catch (err) {
      console.error("Lỗi khi xóa log:", err);
    }
  };

  const fetchAutoSync = async () => {
    try {
      const cfg = await getAutoSyncConfig();
      setAutoSyncConfig(cfg);
      setAutoSyncForm({
        enabled: cfg.enabled,
        interval_minutes: cfg.interval_minutes,
        sync_chains: cfg.sync_chains,
        date_range_days: cfg.date_range_days,
      });
    } catch (err) {
      console.warn('Không thể tải cấu hình tự động đồng bộ:', err);
    }
  };

  useEffect(() => {
    if (!token) return;
    fetchAutoSync();
  }, [token]);

  const handleSaveAutoSync = async () => {
    setIsSavingAutoSync(true);
    setAutoSyncFeedback(null);
    try {
      const updated = await updateAutoSyncConfig(autoSyncForm);
      setAutoSyncConfig(updated);
      setAutoSyncFeedback({
        type: 'success',
        message: autoSyncForm.enabled
          ? `Đã lưu! Quét tự động mỗi ${autoSyncForm.interval_minutes} phút.`
          : 'Đã lưu! Đã tắt quét tự động ngầm.',
      });
      setTimeout(() => setAutoSyncFeedback(null), 4000);
    } catch (err: any) {
      setAutoSyncFeedback({
        type: 'error',
        message: err.message || 'Lỗi khi lưu cấu hình tự động đồng bộ.',
      });
    } finally {
      setIsSavingAutoSync(false);
    }
  };

  const handleTriggerAutoSyncNow = async () => {
    setIsTriggeringAutoSync(true);
    setAutoSyncFeedback(null);
    try {
      const res = await triggerAutoSyncRunNow();
      setAutoSyncFeedback({
        type: 'success',
        message: res.message || 'Đã kích hoạt quét ngầm ngay bây giờ! Chuyển sang tab Nhật ký Log để xem.',
      });
      setTimeout(async () => {
        await fetchLogs();
        const cfg = await getAutoSyncConfig();
        setAutoSyncConfig(cfg);
      }, 3000);
    } catch (err: any) {
      setAutoSyncFeedback({
        type: 'error',
        message: err.message || 'Không thể kích hoạt đồng bộ ngầm.',
      });
    } finally {
      setIsTriggeringAutoSync(false);
    }
  };

  const formatScheduleTime = (isoString?: string | null): string => {
    if (!isoString) return 'Chưa có lịch';
    try {
      const d = parseUtcDate(isoString);
      if (isNaN(d.getTime())) return isoString;
      return d.toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return isoString;
    }
  };

  // Trigger test sync for FPT Shop
  const handleTestSyncFpt = async () => {
    setIsTestingSync(true);
    setTestSyncResult(null);
    try {
      const res = await fetch('/api/admin/test-sync/fpt', { method: 'POST' });
      const data = await res.json();
      setTestSyncResult({
        success: data.success,
        message: data.message || (data.success ? 'Đồng bộ FPT Shop thành công!' : 'Đồng bộ thất bại!')
      });
      await fetchLogs();
      await fetchOverview();
    } catch (err: any) {
      setTestSyncResult({
        success: false,
        message: 'Lỗi khi gọi API chạy thử: ' + (err.message || String(err))
      });
    } finally {
      setIsTestingSync(false);
    }
  };

  // Download log file
  const handleDownloadLogs = () => {
    const textContent = logs.map(l => `[${l.timestamp}] [${l.level}] ${l.logger}: ${l.message}`).join('\n');
    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboardd-logs-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Handle Login
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setIsLoggingIn(true);
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        localStorage.setItem('admin_token', data.token);
        setToken(data.token);
        setPassword('');
      } else {
        setLoginError(data.detail || 'Tài khoản hoặc mật khẩu không đúng!');
      }
    } catch {
      setLoginError('Không thể kết nối đến máy chủ backend!');
    } finally {
      setIsLoggingIn(false);
    }
  };

  // Handle Logout
  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setToken(null);
  };

  // Handle Change Password
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwError('');
    setPwSuccess('');
    try {
      const res = await fetch('/api/admin/change-password', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ old_password: oldPw, new_password: newPw })
      });
      const data = await res.json();
      if (res.ok) {
        setPwSuccess('Đã đổi mật khẩu Admin thành công!');
        setOldPw('');
        setNewPw('');
        setTimeout(() => setIsChangePwOpen(false), 1500);
      } else {
        setPwError(data.detail || 'Đổi mật khẩu thất bại!');
      }
    } catch {
      setPwError('Lỗi kết nối máy chủ!');
    }
  };

  // === RENDER: LOGIN FORM ===
  if (!token) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 font-sans text-slate-100">
        <div className="w-full max-w-sm">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center mb-2">
              <BrandLogo size={40} />
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">Quản trị hệ thống</h1>
            <p className="text-xs text-slate-400 mt-1">Đăng nhập tài khoản Admin để truy cập máy chủ</p>
          </div>

          <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
            <form onSubmit={handleLogin} className="space-y-4">
              {loginError && (
                <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs font-medium">
                  {loginError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">
                  Tài khoản
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500 transition-colors"
                  placeholder="admin"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">
                  Mật khẩu
                </label>
                <div className="relative flex items-center">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-3 pr-9 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500 transition-colors"
                    placeholder="Nhập mật khẩu"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 text-slate-500 hover:text-slate-300 transition-colors text-xs"
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                <div className="mt-1.5 text-[11px] text-slate-500">
                  Mặc định: <span className="text-slate-400 font-mono">admin@123</span>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoggingIn}
                className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl transition-all cursor-pointer disabled:opacity-50"
              >
                {isLoggingIn ? 'Đang xác thực...' : 'Đăng nhập'}
              </button>

              <div className="pt-2 text-center border-t border-slate-800 mt-4">
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="text-xs text-slate-400 hover:text-white transition-colors"
                >
                  ← Quay lại trang Tổng quan
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // === RENDER: STREAMLINED ADMIN DASHBOARD ===
  const sys = overview?.system;
  const db = overview?.database;
  const chains = overview?.chains;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-5">
        
        {/* === TOP ADMIN HEADER (Minimal & Clean) === */}
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 sm:p-5 rounded-2xl">
          <div className="flex items-center gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white tracking-tight">Quản trị hệ thống</h1>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Root Admin
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Trạng thái: <span className="font-semibold text-emerald-400">{sys?.status || 'ONLINE'}</span> (Port {sys?.port || 8000}) · Chạy: <span className="text-slate-300 font-mono">{sys?.uptime_str || '0s'}</span>
              </p>
            </div>
          </div>

          {/* Action Links & Buttons without icons */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                autoRefresh 
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
              }`}
            >
              {autoRefresh ? "• Live 5s" : "Tạm dừng"}
            </button>

            <button
              onClick={fetchOverview}
              disabled={isLoadingOverview}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
            >
              {isLoadingOverview ? "Đang tải..." : "Làm mới"}
            </button>

            <button
              onClick={() => setIsChangePwOpen(true)}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
            >
              Đổi mật khẩu
            </button>

            <button
              onClick={() => navigate('/dashboard')}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
            >
              ← Xem Dashboard
            </button>

            <button
              onClick={handleLogout}
              className="px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 rounded-lg text-xs font-medium border border-rose-500/20 transition-colors"
            >
              Đăng xuất
            </button>
          </div>
        </header>

        {/* === LUCIAN #039 SLIDING PILL TABS === */}
        <div className="flex items-center justify-start border-b border-slate-800 pb-3 gap-2 overflow-x-auto">
          <button
            type="button"
            onClick={() => setActiveTab('system')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'system'
                ? 'bg-white text-slate-950 shadow-sm'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 border border-slate-800/60'
            }`}
          >
            Hệ thống & Kết nối
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('autosync')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === 'autosync'
                ? 'bg-white text-slate-950 shadow-sm'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 border border-slate-800/60'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${autoSyncConfig?.enabled ? 'bg-emerald-500' : 'bg-slate-600'}`} />
            Tự động đồng bộ
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('logs')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === 'logs'
                ? 'bg-white text-slate-950 shadow-sm'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 border border-slate-800/60'
            }`}
          >
            Nhật ký Log ({logs.length})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('audit')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'audit'
                ? 'bg-white text-slate-950 shadow-sm'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 border border-slate-800/60'
            }`}
          >
            Thông báo & Mạng
          </button>
        </div>

        {/* ======================================================== */}
        {/* TAB 1: HỆ THỐNG & KẾT NỐI (Streamlined Metrics) */}
        {/* ======================================================== */}
        {activeTab === 'system' && (
          <div className="space-y-4">
            {/* Server & Hardware Summary */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
              
              {/* Server Status */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Máy chủ</span>
                <div className="text-xl font-bold text-white flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  {sys?.status || 'ONLINE'}
                </div>
                <div className="mt-2 text-[11px] text-slate-400">
                  Cổng: <span className="font-mono text-slate-200 font-bold">{sys?.port || 8000}</span>
                </div>
              </div>

              {/* CPU */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">CPU</span>
                <div className="text-xl font-bold text-white font-mono">{sys?.cpu_percent ?? 0}%</div>
                <div className="w-full bg-slate-800 rounded-full h-1 mt-2.5 overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${
                      (sys?.cpu_percent ?? 0) > 80 ? 'bg-rose-500' : 'bg-indigo-500'
                    }`}
                    style={{ width: `${Math.min(sys?.cpu_percent ?? 0, 100)}%` }}
                  />
                </div>
              </div>

              {/* RAM */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Bộ nhớ RAM</span>
                <div className="text-xl font-bold text-white font-mono">{sys?.ram_percent ?? 0}%</div>
                <div className="mt-1 text-[11px] text-slate-400 font-mono">
                  {sys?.ram_used_gb} / {sys?.ram_total_gb} GB
                </div>
              </div>

              {/* Database */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Cơ sở dữ liệu SQLite</span>
                <div className="text-xl font-bold text-white font-mono">{db?.db_size_mb ?? 0} MB</div>
                <div className="mt-1 text-[11px] text-emerald-400 font-bold">
                  {db?.total_tickets.toLocaleString() ?? 0} dòng dữ liệu
                </div>
              </div>

            </div>

            {/* 3 Chains Status (Clean Flat Table-like Cards) */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800/80">
                <h2 className="text-sm font-bold text-white">Trạng thái kết nối 3 chuỗi</h2>
                <span className="text-xs text-slate-400">Tự động kiểm tra phiên làm việc</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* FPT Shop */}
                <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-white">FPT Shop</span>
                    {chains?.fpt_shop.authenticated ? (
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Đã xác thực
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        {chains?.fpt_shop.status || 'Chưa kết nối'}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 space-y-1">
                    <div className="flex justify-between">
                      <span>Cơ chế:</span>
                      <span className="text-slate-300">Chrome Headless</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Dữ liệu:</span>
                      <span className="font-bold text-rose-400 font-mono">{db?.fpt_tickets.toLocaleString() ?? 0} dòng</span>
                    </div>
                  </div>
                </div>

                {/* Long Châu */}
                <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-white">Long Châu</span>
                    {chains?.long_chau.authenticated ? (
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Đã xác thực
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        {chains?.long_chau.status || 'Chưa kết nối'}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 space-y-1">
                    <div className="flex justify-between">
                      <span>Cơ chế:</span>
                      <span className="text-slate-300">Budibase Session</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Dữ liệu:</span>
                      <span className="font-bold text-blue-400 font-mono">{db?.long_chau_tickets.toLocaleString() ?? 0} dòng</span>
                    </div>
                  </div>
                </div>

                {/* Vaccine */}
                <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-white">Vaccine</span>
                    {chains?.vaccine.authenticated ? (
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Đã xác thực
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        {chains?.vaccine.status || 'Chưa kết nối'}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 space-y-1">
                    <div className="flex justify-between">
                      <span>Cơ chế:</span>
                      <span className="text-slate-300">PTT Public</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Dữ liệu:</span>
                      <span className="font-bold text-teal-400 font-mono">{db?.vaccine_tickets.toLocaleString() ?? 0} dòng</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 2: TỰ ĐỘNG ĐỒNG BỘ (Clean Auto-Sync Scheduler) */}
        {/* ======================================================== */}
        {activeTab === 'autosync' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-bold text-white">Cấu hình tiến trình tự động quét dữ liệu</h2>
                <p className="text-xs text-slate-400 mt-0.5">Hệ thống sẽ chạy ngầm định kỳ để cập nhật số calllog và ticket mới</p>
              </div>

              {autoSyncConfig?.enabled ? (
                <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 self-start sm:self-auto">
                  • Đang bật
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-400 self-start sm:self-auto">
                  Đang tắt
                </span>
              )}
            </div>

            {/* Feedback Alert */}
            {autoSyncFeedback && (
              <div className={`p-3 rounded-xl text-xs font-medium border ${
                autoSyncFeedback.type === 'success' 
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300' 
                  : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
              }`}>
                {autoSyncFeedback.message}
              </div>
            )}

            {/* Inputs Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              
              {/* Toggle Switch */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl flex flex-col justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-300 block mb-1">Trạng thái hoạt động</span>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Bật để server tự động quét định kỳ theo chu kỳ bên dưới.
                  </p>
                </div>
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={() => setAutoSyncForm(prev => ({ ...prev, enabled: !prev.enabled }))}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                      autoSyncForm.enabled 
                        ? 'bg-emerald-600 text-white' 
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {autoSyncForm.enabled ? '✓ Đang kích hoạt' : 'Tắt quét ngầm'}
                  </button>
                </div>
              </div>

              {/* Interval & Days */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl space-y-3">
                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">
                    Chu kỳ quét (phút)
                  </label>
                  <input
                    type="number"
                    min={15}
                    max={1440}
                    value={autoSyncForm.interval_minutes}
                    onChange={(e) => setAutoSyncForm(prev => ({ ...prev, interval_minutes: Number(e.target.value) }))}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-white text-xs font-mono focus:outline-none focus:border-indigo-500"
                  />
                  <span className="text-[10px] text-slate-500 mt-1 block">Khuyến nghị: 60 phút</span>
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-300 block mb-1">
                    Số ngày quét gần nhất
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={90}
                    value={autoSyncForm.date_range_days}
                    onChange={(e) => setAutoSyncForm(prev => ({ ...prev, date_range_days: Number(e.target.value) }))}
                    className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-white text-xs font-mono focus:outline-none focus:border-indigo-500"
                  />
                  <span className="text-[10px] text-slate-500 mt-1 block">Mặc định: 30 ngày gần đây</span>
                </div>
              </div>

              {/* Chain Selection */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2">
                <span className="text-xs font-bold text-slate-300 block mb-1">Chuỗi áp dụng quét ngầm</span>
                {[
                  { key: 'fpt_shop', label: 'FPT Shop' },
                  { key: 'long_chau', label: 'Long Châu' },
                  { key: 'vaccine', label: 'Vaccine' },
                ].map(({ key, label }) => {
                  const checked = autoSyncForm.sync_chains.includes(key);
                  return (
                    <label key={key} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer py-1">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setAutoSyncForm(prev => ({ ...prev, sync_chains: [...prev.sync_chains, key] }));
                          } else {
                            setAutoSyncForm(prev => ({ ...prev, sync_chains: prev.sync_chains.filter(k => k !== key) }));
                          }
                        }}
                        className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                      />
                      <span>{label}</span>
                    </label>
                  );
                })}
              </div>

            </div>

            {/* Schedule Status Strip */}
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <span className="text-slate-400 block text-[11px]">Lần quét gần nhất:</span>
                <span className="font-mono text-slate-200 font-bold">{formatScheduleTime(autoSyncConfig?.last_run_at)}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Lần quét kế tiếp:</span>
                <span className="font-mono text-indigo-400 font-bold">
                  {autoSyncForm.enabled ? formatScheduleTime(autoSyncConfig?.next_run_at) : 'Đang tạm dừng'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Kết quả:</span>
                <span className="text-slate-300 truncate block" title={autoSyncConfig?.last_message || ''}>
                  {autoSyncConfig?.last_message || 'Chưa có dữ liệu'}
                </span>
              </div>
            </div>

            {/* Save & Run Action Buttons */}
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={handleSaveAutoSync}
                disabled={isSavingAutoSync}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl transition-all cursor-pointer disabled:opacity-50"
              >
                {isSavingAutoSync ? 'Đang lưu...' : 'Lưu cấu hình'}
              </button>

              <button
                type="button"
                onClick={handleTriggerAutoSyncNow}
                disabled={isTriggeringAutoSync}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs rounded-xl border border-slate-700 transition-all cursor-pointer disabled:opacity-50"
              >
                {isTriggeringAutoSync ? 'Đang kích hoạt...' : 'Chạy quét ngầm ngay'}
              </button>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 3: NHẬT KÝ LOG (Clean Live Terminal) */}
        {/* ======================================================== */}
        {activeTab === 'logs' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3.5">
            {/* Toolbar */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div className="flex flex-wrap items-center gap-1.5 text-xs">
                <span className="text-slate-400 font-semibold mr-1">Bộ lọc:</span>
                {(['ALL', 'ERROR', 'WARNING', 'INFO'] as const).map(lvl => (
                  <button
                    key={lvl}
                    onClick={() => setLogLevelFilter(lvl)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                      logLevelFilter === lvl
                        ? (lvl === 'ERROR' ? 'bg-rose-500 text-white' :
                           lvl === 'WARNING' ? 'bg-amber-500 text-slate-950' :
                           lvl === 'INFO' ? 'bg-blue-600 text-white' :
                           'bg-white text-slate-950')
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {lvl === 'ALL' ? 'Tất cả' : lvl}
                  </button>
                ))}
              </div>

              {/* Actions */}
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <button
                  onClick={handleTestSyncFpt}
                  disabled={isTestingSync}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-all disabled:opacity-50"
                >
                  {isTestingSync ? 'Đang chạy...' : 'Chạy thử FPT'}
                </button>

                <button
                  onClick={fetchLogs}
                  disabled={isLoadingLogs}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors border border-slate-700"
                >
                  Làm mới
                </button>

                <button
                  onClick={handleClearLogs}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-rose-900/40 text-slate-300 hover:text-rose-300 rounded-lg transition-colors border border-slate-700"
                >
                  Xóa log
                </button>

                <button
                  onClick={handleDownloadLogs}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors border border-slate-700"
                >
                  Tải .txt
                </button>
              </div>
            </div>

            {/* Search & Options Bar */}
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <input
                type="text"
                value={logSearch}
                onChange={(e) => setLogSearch(e.target.value)}
                placeholder="Tìm từ khóa (fpt, error, sync...)"
                className="px-3 py-1 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 w-52 sm:w-64"
              />

              <div className="flex items-center gap-3 text-slate-400">
                <select
                  value={logLinesLimit}
                  onChange={(e) => setLogLinesLimit(Number(e.target.value))}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-slate-300 text-xs focus:outline-none"
                >
                  <option value={100}>100 dòng</option>
                  <option value={200}>200 dòng</option>
                  <option value={500}>500 dòng</option>
                  <option value={1000}>1000 dòng</option>
                </select>

                <label className="flex items-center gap-1.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={autoScrollLogs}
                    onChange={(e) => setAutoScrollLogs(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                  />
                  <span>Tự cuộn</span>
                </label>

                <label className="flex items-center gap-1.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={isAutoRefreshLogs}
                    onChange={(e) => setIsAutoRefreshLogs(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                  />
                  <span>Live</span>
                </label>
              </div>
            </div>

            {/* Test result toast if any */}
            {testSyncResult && (
              <div className={`p-2.5 rounded-lg text-xs font-semibold flex items-center justify-between ${
                testSyncResult.success ? 'bg-emerald-500/10 text-emerald-300' : 'bg-rose-500/10 text-rose-300'
              }`}>
                <span>{testSyncResult.message}</span>
                <button onClick={() => setTestSyncResult(null)} className="text-slate-400 hover:text-white">✕</button>
              </div>
            )}

            {/* Terminal Window */}
            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-3 py-1.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Console Log ({logs.length} dòng)</span>
              </div>
              <div 
                ref={logContainerRef}
                className="p-3 max-h-[460px] overflow-y-auto space-y-0.5 font-mono text-[11px] leading-relaxed"
              >
                {logs.length === 0 ? (
                  <div className="py-10 text-center text-slate-500">
                    Chưa có dòng log nào được ghi nhận.
                  </div>
                ) : (
                  logs.map((log, index) => {
                    const isErr = log.level === 'ERROR' || log.message.toLowerCase().includes('fail') || log.message.toLowerCase().includes('lỗi');
                    const isWarn = log.level === 'WARNING' || log.level === 'WARN';
                    return (
                      <div 
                        key={log.id || index}
                        className={`flex items-start gap-2 py-0.5 px-1 rounded ${
                          isErr ? 'bg-rose-950/20 text-rose-200' :
                          isWarn ? 'bg-amber-950/20 text-amber-200' :
                          'text-slate-300'
                        }`}
                      >
                        <span className="text-slate-600 select-none w-6 text-right shrink-0">{index + 1}</span>
                        <span className="text-slate-500 shrink-0 select-none">[{log.timestamp.slice(11)}]</span>
                        <span className={`px-1 rounded text-[9.5px] font-bold shrink-0 uppercase ${
                          log.level === 'ERROR' ? 'text-rose-400' :
                          log.level === 'WARNING' ? 'text-amber-400' :
                          'text-blue-400'
                        }`}>
                          {log.level}
                        </span>
                        <span className="text-indigo-400 shrink-0 hidden sm:inline select-none">
                          [{log.logger.replace('app.services.', '').replace('app.api.', '')}]
                        </span>
                        <span className="break-all whitespace-pre-wrap flex-1">{log.message}</span>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 4: THÔNG BÁO & MẠNG (Clean Activity & LAN Access) */}
        {/* ======================================================== */}
        {activeTab === 'audit' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            
            {/* Recent Notifications (Clean list matching image) */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h2 className="text-sm font-bold text-white">Lịch sử thông báo đồng bộ</h2>
                <span className="text-[11px] text-slate-400">10 sự kiện gần nhất</span>
              </div>

              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {overview?.recent_notifications && overview.recent_notifications.length > 0 ? (
                  overview.recent_notifications.map(n => (
                    <div key={n.id} className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-200">{n.title}</span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {n.created_at ? parseUtcDate(n.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) : ''}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">{n.message}</p>
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-slate-500 text-xs">
                    Chưa có thông báo nào
                  </div>
                )}
              </div>
            </div>

            {/* Network Access */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between space-y-4">
              <div>
                <div className="pb-2 border-b border-slate-800 mb-3">
                  <h2 className="text-sm font-bold text-white">Đường dẫn truy cập hệ thống</h2>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                    <span className="font-bold text-slate-300 block">Đường dẫn mạng nội bộ (LAN):</span>
                    <div className="font-mono text-slate-200 bg-slate-900 px-2.5 py-1.5 rounded border border-slate-800 select-all">
                      http://10.96.25.111:8000
                    </div>
                    <p className="text-[11px] text-slate-400">Dành cho các máy tính chung phòng mạng nội bộ.</p>
                  </div>

                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                    <span className="font-bold text-slate-300 block">Đường dẫn Tên miền chính thức:</span>
                    <div className="font-mono text-slate-200 bg-slate-900 px-2.5 py-1.5 rounded border border-slate-800 select-all">
                      https://tophoploi.site
                    </div>
                    <p className="text-[11px] text-slate-400">Truy cập từ mọi nơi có kết nối internet.</p>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span>DashBoardD Enterprise</span>
                <span className="text-[11px] text-slate-500">
                  Cập nhật: {new Date(overview?.checked_at || Date.now()).toLocaleTimeString()}
                </span>
              </div>
            </div>

          </div>
        )}

      </div>

      {/* === MODAL: CHANGE PASSWORD === */}
      {isChangePwOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-sm p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-sm">Đổi mật khẩu Admin</h3>
              <button onClick={() => setIsChangePwOpen(false)} className="text-slate-400 hover:text-white text-xs">✕</button>
            </div>

            {pwError && (
              <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs">
                {pwError}
              </div>
            )}
            {pwSuccess && (
              <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs">
                {pwSuccess}
              </div>
            )}

            <form onSubmit={handleChangePassword} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Mật khẩu cũ</label>
                <input 
                  type="password" 
                  value={oldPw}
                  onChange={e => setOldPw(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Mật khẩu mới</label>
                <input 
                  type="password" 
                  value={newPw}
                  onChange={e => setNewPw(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                  placeholder="Tối thiểu 6 ký tự"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsChangePwOpen(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-lg text-xs"
                >
                  Lưu mật khẩu
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default Admin;
