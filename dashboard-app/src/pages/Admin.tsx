import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Shield, Server, Cpu, Database, RefreshCw, Key, LogOut, 
  AlertTriangle, Clock, Activity, ArrowLeft, 
  Eye, EyeOff, Lock, User, HardDrive, Wifi, Store, Pill, 
  ShieldPlus, Bell, CheckCircle2, Terminal, Play, Trash2, Download, Search, AlertCircle, XCircle
} from 'lucide-react';
import { GlassCard } from '../components/common/GlassCard';
import BrandLogo from '../components/common/BrandLogo';

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

const Admin: React.FC = () => {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('admin_token'));
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

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
  const logContainerRef = React.useRef<HTMLDivElement>(null);

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
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4 relative overflow-hidden font-sans">
        {/* Background glow effects */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/15 rounded-full blur-3xl pointer-events-none" />

        <div className="w-full max-w-md relative z-10">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center p-3 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl mb-3">
              <BrandLogo size={42} />
            </div>
            <h1 className="text-2xl font-black text-white tracking-tight">Trung Tâm Quản Trị</h1>
            <p className="text-sm text-slate-400 mt-1">Đăng nhập tài khoản Admin để theo dõi hệ thống DashBoardD</p>
          </div>

          <GlassCard className="p-7 backdrop-blur-2xl bg-slate-800/80 border border-slate-700/80 shadow-2xl rounded-2xl">
            <form onSubmit={handleLogin} className="space-y-4">
              {loginError && (
                <div className="p-3 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-300 text-xs font-semibold flex items-center gap-2">
                  <AlertTriangle size={16} className="shrink-0 text-rose-400" />
                  <span>{loginError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                  Tài khoản Admin
                </label>
                <div className="relative flex items-center">
                  <User size={17} className="absolute left-3 text-slate-400" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-9 pr-4 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                    placeholder="Tên đăng nhập (admin)"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                  Mật khẩu
                </label>
                <div className="relative flex items-center">
                  <Lock size={17} className="absolute left-3 text-slate-400" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-10 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                    placeholder="Nhập mật khẩu Admin"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                <div className="mt-2 text-[11px] text-slate-500 flex items-center justify-between">
                  <span>Mật khẩu mặc định: <strong className="text-slate-400 font-mono">admin@123</strong></span>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoggingIn}
                className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm rounded-xl shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-98 disabled:opacity-50"
              >
                {isLoggingIn ? (
                  <RefreshCw size={17} className="animate-spin" />
                ) : (
                  <Shield size={17} />
                )}
                {isLoggingIn ? 'Đang xác thực...' : 'Đăng nhập Quản Trị'}
              </button>

              <div className="pt-2 text-center border-t border-slate-700/60 mt-4">
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="text-xs text-slate-400 hover:text-white transition-colors inline-flex items-center gap-1.5"
                >
                  <ArrowLeft size={14} /> Quay lại trang Dashboard chính
                </button>
              </div>
            </form>
          </GlassCard>
        </div>
      </div>
    );
  }

  // === RENDER: ADMIN DASHBOARD MONITOR ===
  const sys = overview?.system;
  const db = overview?.database;
  const chains = overview?.chains;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-4 sm:p-6 lg:p-8 relative">
      {/* Dynamic Background Glow */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none overflow-hidden z-0">
        <div className="absolute top-10 left-1/3 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] bg-indigo-600/10 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto relative z-10 space-y-6">
        
        {/* === TOP ADMIN HEADER === */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 backdrop-blur-xl border border-slate-800 p-4 sm:p-5 rounded-2xl shadow-xl">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-xl shadow-lg shadow-indigo-500/20 text-white">
              <Shield size={24} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-black text-white tracking-tight">Khu Vực Quản Trị Hệ Thống</h1>
                <span className="px-2 py-0.5 text-[11px] font-extrabold uppercase rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Root Admin
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">Giám sát máy chủ nội bộ, tiến trình đồng bộ dữ liệu và bảo mật</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                autoRefresh 
                  ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-300' 
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
              }`}
              title="Tự động cập nhật mỗi 5 giây"
            >
              <RefreshCw size={14} className={autoRefresh ? "animate-spin" : ""} />
              {autoRefresh ? "Live 5s" : "Tạm dừng"}
            </button>

            <button
              onClick={fetchOverview}
              disabled={isLoadingOverview}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1.5"
            >
              <RefreshCw size={14} className={isLoadingOverview ? "animate-spin" : ""} /> Làm mới
            </button>

            <button
              onClick={() => setIsChangePwOpen(true)}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1.5"
            >
              <Key size={14} /> Đổi mật khẩu
            </button>

            <button
              onClick={() => navigate('/dashboard')}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1.5"
            >
              <ArrowLeft size={14} /> Xem Dashboard
            </button>

            <button
              onClick={handleLogout}
              className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 rounded-xl text-xs font-semibold border border-rose-500/30 transition-colors flex items-center gap-1.5"
            >
              <LogOut size={14} /> Đăng xuất
            </button>
          </div>
        </header>

        {/* === SECTION 1: SERVER & HARDWARE METRICS === */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Card 1: Server Status */}
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-4.5 backdrop-blur-xl">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Trạng Thái Server</span>
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl">
                <Server size={18} />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-white">{sys?.status || 'ONLINE'}</span>
              <span className="text-xs font-medium text-emerald-400 font-mono">Port {sys?.port || 8000}</span>
            </div>
            <div className="mt-2 text-[12px] text-slate-400 flex items-center gap-1.5">
              <Clock size={13} className="text-slate-500" />
              <span>Thời gian chạy: <strong className="text-slate-300 font-mono">{sys?.uptime_str || '0s'}</strong></span>
            </div>
          </div>

          {/* Card 2: CPU Usage */}
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-4.5 backdrop-blur-xl">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Sử Dụng CPU</span>
              <div className="p-2 bg-blue-500/10 text-blue-400 rounded-xl">
                <Cpu size={18} />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-white font-mono">{sys?.cpu_percent ?? 0}%</span>
              <span className="text-xs text-slate-400">Máy trạm nội bộ</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${
                  (sys?.cpu_percent ?? 0) > 80 ? 'bg-rose-500' : (sys?.cpu_percent ?? 0) > 50 ? 'bg-amber-500' : 'bg-blue-500'
                }`}
                style={{ width: `${Math.min(sys?.cpu_percent ?? 0, 100)}%` }}
              />
            </div>
          </div>

          {/* Card 3: RAM Usage */}
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-4.5 backdrop-blur-xl">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Bộ Nhớ RAM</span>
              <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl">
                <HardDrive size={18} />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-white font-mono">{sys?.ram_percent ?? 0}%</span>
              <span className="text-xs text-slate-400 font-mono">({sys?.ram_used_gb} / {sys?.ram_total_gb} GB)</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${
                  (sys?.ram_percent ?? 0) > 85 ? 'bg-rose-500' : (sys?.ram_percent ?? 0) > 70 ? 'bg-amber-500' : 'bg-indigo-500'
                }`}
                style={{ width: `${Math.min(sys?.ram_percent ?? 0, 100)}%` }}
              />
            </div>
          </div>

          {/* Card 4: Database Storage */}
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-4.5 backdrop-blur-xl">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Cơ Sở Dữ Liệu SQLite</span>
              <div className="p-2 bg-amber-500/10 text-amber-400 rounded-xl">
                <Database size={18} />
              </div>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-white font-mono">{db?.db_size_mb ?? 0} MB</span>
              <span className="text-xs text-emerald-400 font-bold">{db?.total_tickets.toLocaleString() ?? 0} tickets</span>
            </div>
            <div className="mt-2 text-[12px] text-slate-400 flex items-center justify-between">
              <span>Đang lưu tại:</span>
              <span className="text-slate-300 font-mono text-[11px]">opsmonitor.db</span>
            </div>
          </div>

        </div>

        {/* === SECTION 2: 3 CHAINS CONNECTION STATUS === */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Wifi size={18} className="text-indigo-400" />
              <h2 className="text-base font-bold text-white">Trạng Thái Kết Nối 3 Chuỗi (Selenium & Budibase)</h2>
            </div>
            <span className="text-xs text-slate-400">Kiểm tra phiên đăng nhập tự động</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* Chain 1: FPT Shop */}
            <div className="p-4 bg-slate-950/70 border border-slate-800/90 rounded-xl relative overflow-hidden">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-rose-500/10 text-rose-400 rounded-lg">
                    <Store size={18} />
                  </div>
                  <span className="font-bold text-sm text-white">FPT Shop</span>
                </div>
                {chains?.fpt_shop.authenticated ? (
                  <span className="px-2 py-0.5 text-[11px] font-bold rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                    <CheckCircle2 size={12} /> Connected
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[11px] font-bold rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                    <Clock size={12} /> {chains?.fpt_shop.status || 'Chưa kết nối'}
                  </span>
                )}
              </div>
              <div className="mt-3 text-xs text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span>Trình duyệt:</span>
                  <span className="font-mono text-slate-300">Chrome Headless</span>
                </div>
                <div className="flex justify-between">
                  <span>Dữ liệu đã nạp:</span>
                  <span className="font-bold text-rose-400 font-mono">{db?.fpt_tickets.toLocaleString() ?? 0} dòng</span>
                </div>
              </div>
            </div>

            {/* Chain 2: Long Châu */}
            <div className="p-4 bg-slate-950/70 border border-slate-800/90 rounded-xl relative overflow-hidden">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-blue-500/10 text-blue-400 rounded-lg">
                    <Pill size={18} />
                  </div>
                  <span className="font-bold text-sm text-white">Long Châu</span>
                </div>
                {chains?.long_chau.authenticated ? (
                  <span className="px-2 py-0.5 text-[11px] font-bold rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                    <CheckCircle2 size={12} /> Connected
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[11px] font-bold rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                    <Clock size={12} /> {chains?.long_chau.status || 'Chưa kết nối'}
                  </span>
                )}
              </div>
              <div className="mt-3 text-xs text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span>Cơ chế:</span>
                  <span className="font-mono text-slate-300">Budibase API Session</span>
                </div>
                <div className="flex justify-between">
                  <span>Dữ liệu đã nạp:</span>
                  <span className="font-bold text-blue-400 font-mono">{db?.long_chau_tickets.toLocaleString() ?? 0} dòng</span>
                </div>
              </div>
            </div>

            {/* Chain 3: Vaccine */}
            <div className="p-4 bg-slate-950/70 border border-slate-800/90 rounded-xl relative overflow-hidden">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-teal-500/10 text-teal-400 rounded-lg">
                    <ShieldPlus size={18} />
                  </div>
                  <span className="font-bold text-sm text-white">Vaccine</span>
                </div>
                {chains?.vaccine.authenticated ? (
                  <span className="px-2 py-0.5 text-[11px] font-bold rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                    <CheckCircle2 size={12} /> Connected
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[11px] font-bold rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                    <Clock size={12} /> {chains?.vaccine.status || 'Chưa kết nối'}
                  </span>
                )}
              </div>
              <div className="mt-3 text-xs text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span>Cơ chế:</span>
                  <span className="font-mono text-slate-300">PTT Public Datasource</span>
                </div>
                <div className="flex justify-between">
                  <span>Dữ liệu đã nạp:</span>
                  <span className="font-bold text-teal-400 font-mono">{db?.vaccine_tickets.toLocaleString() ?? 0} dòng</span>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* === SECTION 2.5: LIVE LOG CONSOLE & SYNC DIAGNOSTICS === */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 backdrop-blur-xl shadow-2xl space-y-4">
          
          {/* Header & Controls */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-xl flex items-center justify-center">
                <Terminal size={22} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-black text-white tracking-tight">Nhật Ký Hệ Thống & Đồng Bộ (Live Console)</h2>
                  <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold flex items-center gap-1.5 ${
                    isAutoRefreshLogs ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'
                  }`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${isAutoRefreshLogs ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                    {isAutoRefreshLogs ? 'Live 2.5s' : 'Đã dừng'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">Theo dõi trực tiếp từng bước kết nối Selenium, tải file Excel và gọi API FPT / Long Châu / Vaccine</p>
              </div>
            </div>

            {/* Quick Actions & Trigger Test Sync */}
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleTestSyncFpt}
                disabled={isTestingSync}
                className="px-3.5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
                title="Bấm để kích hoạt đồng bộ FPT ngay lập tức và xem log trực tiếp"
              >
                {isTestingSync ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} fill="currentColor" />}
                {isTestingSync ? 'Đang chạy đồng bộ FPT...' : '⚡ Chạy Thử Đồng Bộ FPT Ngay'}
              </button>

              <button
                onClick={fetchLogs}
                disabled={isLoadingLogs}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1.5 cursor-pointer"
                title="Tải lại log"
              >
                <RefreshCw size={14} className={isLoadingLogs ? "animate-spin" : ""} />
                Làm mới
              </button>

              <button
                onClick={handleClearLogs}
                className="px-3 py-2 bg-slate-800 hover:bg-rose-900/40 text-slate-300 hover:text-rose-300 rounded-xl text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1.5 cursor-pointer"
                title="Xóa log hiện tại"
              >
                <Trash2 size={14} />
                Xóa log
              </button>

              <button
                onClick={handleDownloadLogs}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1.5 cursor-pointer"
                title="Tải file log về máy"
              >
                <Download size={14} />
                Tải log (.txt)
              </button>
            </div>
          </div>

          {/* Test Sync Banner Result if triggered */}
          {testSyncResult && (
            <div className={`p-3 rounded-xl border text-xs font-semibold flex items-center justify-between gap-3 ${
              testSyncResult.success 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
                : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
            }`}>
              <div className="flex items-center gap-2">
                {testSyncResult.success ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                <span><strong>Kết quả chạy thử FPT:</strong> {testSyncResult.message}</span>
              </div>
              <button onClick={() => setTestSyncResult(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>
          )}

          {/* Filter Bar & Options */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            
            {/* Level Filters */}
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-slate-400 font-bold mr-1">Bộ lọc:</span>
              {(['ALL', 'ERROR', 'WARNING', 'INFO'] as const).map(lvl => (
                <button
                  key={lvl}
                  onClick={() => setLogLevelFilter(lvl)}
                  className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
                    logLevelFilter === lvl
                      ? (lvl === 'ERROR' ? 'bg-rose-500 text-white shadow' :
                         lvl === 'WARNING' ? 'bg-amber-500 text-slate-950 shadow' :
                         lvl === 'INFO' ? 'bg-blue-600 text-white shadow' :
                         'bg-slate-200 text-slate-900 shadow')
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
                  }`}
                >
                  {lvl === 'ALL' ? 'Tất cả' : lvl}
                </button>
              ))}
            </div>

            {/* Search Box & Auto-scroll Toggle */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={logSearch}
                  onChange={(e) => setLogSearch(e.target.value)}
                  placeholder="Lọc từ khóa (fpt, error, sync...)"
                  className="pl-8 pr-3 py-1 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 w-48 sm:w-56"
                />
                {logSearch && (
                  <button 
                    onClick={() => setLogSearch('')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white text-xs"
                  >
                    ✕
                  </button>
                )}
              </div>

              <select
                value={logLinesLimit}
                onChange={(e) => setLogLinesLimit(Number(e.target.value))}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-slate-300 text-xs focus:outline-none focus:border-indigo-500"
              >
                <option value={100}>100 dòng</option>
                <option value={200}>200 dòng</option>
                <option value={500}>500 dòng</option>
                <option value={1000}>1000 dòng</option>
              </select>

              <label className="flex items-center gap-1.5 text-slate-400 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={autoScrollLogs}
                  onChange={(e) => setAutoScrollLogs(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                />
                <span>Cuộn tự động</span>
              </label>

              <label className="flex items-center gap-1.5 text-slate-400 cursor-pointer select-none">
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

          {/* Terminal Display */}
          <div className="bg-slate-950/95 border border-slate-800/90 rounded-xl overflow-hidden shadow-inner">
            
            {/* Terminal Window Top Bar */}
            <div className="px-3 py-2 bg-slate-900 border-b border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block"></span>
                <span className="ml-2 text-slate-400 font-bold">opsmonitor-daemon@server: ~/logs</span>
              </div>
              <div className="flex items-center gap-2">
                <span>Hiển thị: <strong>{logs.length}</strong> dòng</span>
              </div>
            </div>

            {/* Terminal Log Lines Body */}
            <div 
              ref={logContainerRef}
              className="p-3.5 max-h-[380px] overflow-y-auto space-y-1 font-mono text-[11px] leading-relaxed selection:bg-indigo-500 selection:text-white"
            >
              {logs.length === 0 ? (
                <div className="py-12 text-center text-slate-500 space-y-1">
                  <Terminal size={24} className="mx-auto text-slate-600" />
                  <p>Chưa có log nào được ghi nhận hoặc không khớp với bộ lọc.</p>
                  <p className="text-[10px] text-slate-600">Bấm "⚡ Chạy Thử Đồng Bộ FPT Ngay" ở trên để kiểm tra kết nối.</p>
                </div>
              ) : (
                logs.map((log, index) => {
                  const isErr = log.level === 'ERROR' || log.message.toLowerCase().includes('fail') || log.message.toLowerCase().includes('lỗi');
                  const isWarn = log.level === 'WARNING' || log.level === 'WARN';
                  const isSuccess = log.message.toLowerCase().includes('thành công') || log.message.toLowerCase().includes('succeeded') || log.message.toLowerCase().includes('complete');
                  
                  return (
                    <div 
                      key={log.id || index}
                      className={`flex items-start gap-2 py-0.5 px-1.5 rounded transition-colors hover:bg-slate-900/60 ${
                        isErr ? 'bg-rose-950/20 text-rose-200' :
                        isWarn ? 'bg-amber-950/20 text-amber-200' :
                        isSuccess ? 'bg-emerald-950/20 text-emerald-200' :
                        'text-slate-300'
                      }`}
                    >
                      {/* Line Number */}
                      <span className="text-slate-600 select-none w-7 text-right shrink-0">{index + 1}</span>
                      
                      {/* Timestamp */}
                      <span className="text-slate-500 shrink-0 select-none">[{log.timestamp.slice(11)}]</span>
                      
                      {/* Level Badge */}
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 select-none uppercase ${
                        log.level === 'ERROR' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                        log.level === 'WARNING' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                        log.level === 'DEBUG' ? 'bg-slate-800 text-slate-400' :
                        'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}>
                        {log.level}
                      </span>

                      {/* Logger Module */}
                      <span className="text-indigo-400 shrink-0 hidden sm:inline select-none">
                        [{log.logger.replace('app.services.', '').replace('app.api.', '')}]:
                      </span>

                      {/* Message */}
                      <span className="break-all whitespace-pre-wrap flex-1">
                        {log.message}
                      </span>
                    </div>
                  );
                })
              )}
            </div>

          </div>

        </div>

        {/* === SECTION 3: SYSTEM AUDIT & RECENT NOTIFICATIONS === */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          
          {/* Left: Recent Notifications / Sync Events */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-3.5">
              <div className="flex items-center gap-2">
                <Bell size={18} className="text-amber-400" />
                <h2 className="text-sm font-bold text-white">Thông Báo Hoạt Động Mới Nhất</h2>
              </div>
              <span className="text-[11px] text-slate-400">Ghi nhận từ hệ thống</span>
            </div>

            <div className="space-y-2.5 max-h-[320px] overflow-y-auto pr-1">
              {overview?.recent_notifications && overview.recent_notifications.length > 0 ? (
                overview.recent_notifications.map(n => (
                  <div key={n.id} className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs flex items-start justify-between gap-3">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-200">{n.title}</span>
                        {n.chain && (
                          <span className="px-1.5 py-0.2 bg-slate-800 text-[10px] text-slate-400 rounded">
                            {n.chain}
                          </span>
                        )}
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">{n.message}</p>
                    </div>
                    <span className="text-[10px] text-slate-500 shrink-0 font-mono">
                      {n.created_at ? new Date(n.created_at).toLocaleTimeString() : ''}
                    </span>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-slate-500 text-xs">
                  Chưa có thông báo mới nào
                </div>
              )}
            </div>
          </div>

          {/* Right: Network & Access Tips for Admin */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 backdrop-blur-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3.5">
                <div className="flex items-center gap-2">
                  <Activity size={18} className="text-blue-400" />
                  <h2 className="text-sm font-bold text-white">Thông Tin Mạng & Vận Hành Cho Admin</h2>
                </div>
                <span className="text-[11px] text-slate-400">Bảo mật</span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                  <div className="font-bold text-blue-300 mb-1 flex items-center gap-1.5">
                    <Wifi size={14} /> Đường dẫn nội bộ cho văn phòng:
                  </div>
                  <div className="font-mono text-slate-200 bg-slate-950/60 p-2 rounded-lg border border-slate-800 select-all">
                    http://10.96.25.111:8000
                  </div>
                  <p className="text-[11px] text-blue-400/80 mt-1">Dành cho 2 máy tính trong phòng, tốc độ tức thì, không cần mật khẩu IP.</p>
                </div>

                <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
                  <div className="font-bold text-indigo-300 mb-1 flex items-center gap-1.5">
                    <Shield size={14} /> Đường dẫn Admin Bí Mật:
                  </div>
                  <div className="font-mono text-slate-200 bg-slate-950/60 p-2 rounded-lg border border-slate-800 select-all">
                    {window.location.origin}/#/admin
                  </div>
                  <p className="text-[11px] text-indigo-400/80 mt-1">Chỉ bạn biết đường link này để vào kiểm tra máy chủ và giám sát.</p>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <span>Phiên bản: <strong className="text-slate-200">DashBoardD v2.4 Enterprise</strong></span>
              <span className="text-[11px] text-slate-500">Cập nhật: {new Date(overview?.checked_at || Date.now()).toLocaleTimeString()}</span>
            </div>
          </div>

        </div>

      </div>

      {/* === MODAL: CHANGE PASSWORD === */}
      {isChangePwOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-sm p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <Key size={18} className="text-indigo-400" /> Đổi Mật Khẩu Admin
              </h3>
              <button onClick={() => setIsChangePwOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleChangePassword} className="space-y-3">
              {pwError && (
                <div className="p-2.5 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-300 text-xs font-semibold">
                  {pwError}
                </div>
              )}
              {pwSuccess && (
                <div className="p-2.5 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs font-semibold">
                  {pwSuccess}
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">Mật khẩu hiện tại</label>
                <input
                  type="password"
                  value={oldPw}
                  onChange={(e) => setOldPw(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-1">Mật khẩu mới</label>
                <input
                  type="password"
                  value={newPw}
                  onChange={(e) => setNewPw(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                  placeholder="Ít nhất 4 ký tự"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsChangePwOpen(false)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded-xl text-xs font-semibold"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold"
                >
                  Lưu mật khẩu mới
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
