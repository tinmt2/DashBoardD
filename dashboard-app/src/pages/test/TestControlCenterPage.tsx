import React, { useState, useEffect } from 'react';
import { useNavigate, NavLink } from 'react-router-dom';
import { 
  Camera, 
  Ticket, 
  Activity, 
  MessageSquare, 
  Sliders, 
  ShieldAlert, 
  Server, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ArrowRight, 
  Database, 
  Wifi, 
  WifiOff, 
  Layers,
  FileSpreadsheet,
  User
} from 'lucide-react';
import { testApiClient } from '../../services/testApi/client';
import { cameraApi } from '../../services/testApi/cameraApi';
import { ftelDvrApi } from '../../services/testApi/ftelDvrApi';
import { zaloApi } from '../../services/testApi/zaloApi';
import { getTestApiBaseUrl } from '../../services/testApi/config';

interface BackendHealthInfo {
  online: boolean;
  service: string | null;
  latencyMs: number;
  error?: string;
}

interface WarehouseInfo {
  status: string;
  totalCount: number;
  lcCount: number;
  vxCount: number;
  lastSync: string | null;
}

interface DvrStatusInfo {
  status: string;
  progress: number;
  total: number;
}

interface ZaloStatusInfo {
  isMonitoring: boolean;
  activeGroup: string;
  totalDetected: number;
  totalSynced: number;
}

export const TestControlCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const testBaseUrl = getTestApiBaseUrl();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastCheckTime, setLastCheckTime] = useState<string>('');

  const [healthInfo, setHealthInfo] = useState<BackendHealthInfo>({
    online: false,
    service: null,
    latencyMs: 0,
  });

  const [warehouseInfo, setWarehouseInfo] = useState<WarehouseInfo>({
    status: 'checking',
    totalCount: 0,
    lcCount: 0,
    vxCount: 0,
    lastSync: null,
  });

  const [dvrInfo, setDvrInfo] = useState<DvrStatusInfo>({
    status: 'unknown',
    progress: 0,
    total: 0,
  });

  const [zaloInfo, setZaloInfo] = useState<ZaloStatusInfo>({
    isMonitoring: false,
    activeGroup: '',
    totalDetected: 0,
    totalSynced: 0,
  });

  const loadStatusData = async () => {
    const startTime = performance.now();
    try {
      // 1. Check Backend Health
      const healthRes = await testApiClient<{ service: string }>('/health', { timeout: 3000 });
      const latency = Math.round(performance.now() - startTime);

      if (healthRes.success && (healthRes.status === 'ok' || (healthRes as any).status === 'healthy')) {
        setHealthInfo({
          online: true,
          service: healthRes.service || 'test-python-backend',
          latencyMs: latency,
        });

        // 2. Fetch Warehouse Status
        try {
          const whRes = await cameraApi.getWarehouseStatus();
          if (whRes.success && whRes.data) {
            const data = whRes.data;
            setWarehouseInfo({
              status: data.status || 'ready',
              totalCount: data.count || 0,
              lcCount: data.counts_by_mode?.cam_lc || 0,
              vxCount: data.counts_by_mode?.cam_vx || 0,
              lastSync: data.last_sync || null,
            });
          }
        } catch {
          // ignore warehouse fetch fail
        }

        // 3. Fetch FTEL DVR Status
        try {
          const dvrRes = await ftelDvrApi.getStatus();
          if (dvrRes.success && dvrRes.data) {
            const data = dvrRes.data as any;
            setDvrInfo({
              status: data.status || (data.is_running ? 'running' : 'idle'),
              progress: data.progress || data.current || 0,
              total: data.total || 0,
            });
          }
        } catch {
          // ignore dvr fetch fail
        }

        // 4. Fetch Zalo Monitor Status
        try {
          const zaloRes = await zaloApi.getStatus(false);
          if (zaloRes.success && zaloRes.data) {
            const data = zaloRes.data as any;
            setZaloInfo({
              isMonitoring: Boolean(data.is_monitoring),
              activeGroup: data.adapter_status?.active_group || data.fixed_group_name || 'GS AN NINH',
              totalDetected: data.stats?.total_detected || 0,
              totalSynced: data.stats?.total_synced || 0,
            });
          }
        } catch {
          // ignore zalo fetch fail
        }
      } else {
        setHealthInfo({
          online: false,
          service: null,
          latencyMs: latency,
          error: healthRes.message || 'Backend phản hồi không đúng chuẩn',
        });
      }
    } catch (err: any) {
      setHealthInfo({
        online: false,
        service: null,
        latencyMs: 0,
        error: err.message || 'Không thể kết nối đến backend Test (18020)',
      });
    } finally {
      setLastCheckTime(new Date().toLocaleTimeString('vi-VN'));
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadStatusData();
    const interval = setInterval(loadStatusData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadStatusData();
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* === TOP HEADER & INTERNAL SUB-NAV === */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                <ShieldAlert size={22} strokeWidth={2.3} />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
                  Test Operations Control Center
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Trung tâm điều phối các tác vụ kiểm tra camera, FTEL DVR, Ticket SSC và Giám sát Zalo
                </p>
              </div>
            </div>
          </div>

          {/* Connection status badge & Refresh */}
          <div className="flex items-center gap-2.5 self-start sm:self-auto">
            <div className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 border ${
              healthInfo.online
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/60'
                : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800/60'
            }`}>
              {healthInfo.online ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Test Backend: Online ({healthInfo.latencyMs}ms)</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  <span>Test Backend: Ngắt kết nối</span>
                </>
              )}
            </div>

            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-2 rounded-xl bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition-colors shadow-xs cursor-pointer"
              title="Làm mới trạng thái"
            >
              <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Sub-Navigation Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 pt-1 border-b border-slate-200 dark:border-slate-800 text-xs font-bold scrollbar-none">
          <NavLink
            to="/admin"
            end
            className={({ isActive }) => `px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              isActive 
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950 shadow-xs' 
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Layers size={14} />
            <span>Tổng quan Test</span>
          </NavLink>

          <NavLink
            to="/admin/camera"
            className={({ isActive }) => `px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              isActive 
                ? 'bg-blue-600 text-white shadow-xs' 
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Camera size={14} />
            <span>Check Camera</span>
          </NavLink>

          <NavLink
            to="/admin/ticket"
            className={({ isActive }) => `px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              isActive 
                ? 'bg-indigo-600 text-white shadow-xs' 
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Ticket size={14} />
            <span>Ticket SSC</span>
          </NavLink>

          <NavLink
            to="/admin/motion"
            className={({ isActive }) => `px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              isActive 
                ? 'bg-teal-600 text-white shadow-xs' 
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Activity size={14} />
            <span>Motion Analytics</span>
          </NavLink>

          <NavLink
            to="/admin/zalo"
            className={({ isActive }) => `px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              isActive 
                ? 'bg-rose-600 text-white shadow-xs' 
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <MessageSquare size={14} />
            <span>Zalo Monitor</span>
          </NavLink>

          <NavLink
            to="/admin/settings"
            className={({ isActive }) => `px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              isActive 
                ? 'bg-violet-600 text-white shadow-xs' 
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Sliders size={14} />
            <span>Cài đặt Test</span>
          </NavLink>

          <div className="h-4 w-px bg-slate-300 dark:bg-slate-700 mx-1 shrink-0" />

          <NavLink
            to="/admin/system"
            className={({ isActive }) => `px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              isActive 
                ? 'bg-amber-600 text-white shadow-xs' 
                : 'text-amber-700 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/30'
            }`}
            title="Quản trị hệ thống DashboardD (Auto-Sync, TOTP, Logs)"
          >
            <Server size={14} />
            <span>Quản trị Hệ thống</span>
          </NavLink>

          <NavLink
            to="/admin/system?tab=inside"
            className="px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap cursor-pointer text-amber-700 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/30"
            title="Cài đặt tài khoản Inside cho 3 chuỗi"
          >
            <User size={14} />
            <span>Tài khoản Inside</span>
          </NavLink>
        </div>
      </div>

      {/* === WARNING BANNER IF BACKEND OFFLINE === */}
      {!healthInfo.online && !loading && (
        <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 flex items-start gap-3">
          <AlertCircle size={20} className="text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-rose-900 dark:text-rose-200">
              Không thể kết nối đến Backend Test Engine (18020)
            </h4>
            <p className="text-xs text-rose-700 dark:text-rose-400">
              Vui lòng đảm bảo tiến trình backend đang chạy tại địa chỉ <code className="px-1.5 py-0.5 bg-rose-100 dark:bg-rose-900/60 rounded font-mono">{testBaseUrl}</code>. Bạn có thể khởi động backend độc lập bằng file <code className="px-1.5 py-0.5 bg-rose-100 dark:bg-rose-900/60 rounded font-mono">scripts/start_backend.bat</code>.
            </p>
          </div>
        </div>
      )}

      {/* === METRIC STATUS CARDS (REAL DATA ONLY) === */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Backend Connection */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Test Backend</span>
            <div className={`p-1.5 rounded-lg ${healthInfo.online ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'}`}>
              {healthInfo.online ? <Wifi size={16} /> : <WifiOff size={16} />}
            </div>
          </div>
          <div>
            <div className="text-xl font-black text-slate-900 dark:text-white">
              {healthInfo.online ? '127.0.0.1:18020' : 'Offline'}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-1.5">
              <span>Độ trễ: {healthInfo.online ? `${healthInfo.latencyMs}ms` : 'N/A'}</span>
              <span>•</span>
              <span className="truncate">{healthInfo.service || 'Test API'}</span>
            </div>
          </div>
        </div>

        {/* Card 2: Warehouse Status */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Kho Cửa Hàng</span>
            <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-500">
              <Database size={16} />
            </div>
          </div>
          <div>
            <div className="text-xl font-black text-slate-900 dark:text-white">
              {warehouseInfo.totalCount > 0 ? warehouseInfo.totalCount.toLocaleString() : '---'}
              <span className="text-xs font-medium text-slate-400 ml-1">shop</span>
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              <span>LC: {warehouseInfo.lcCount}</span>
              <span className="mx-1">•</span>
              <span>VX: {warehouseInfo.vxCount}</span>
              <span className="mx-1">•</span>
              <span className="text-emerald-500 font-medium capitalize">{warehouseInfo.status}</span>
            </div>
          </div>
        </div>

        {/* Card 3: FTEL DVR Scanner */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">FTEL DVR Scanner</span>
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-500">
              <Activity size={16} />
            </div>
          </div>
          <div>
            <div className="text-xl font-black text-slate-900 dark:text-white capitalize">
              {dvrInfo.status === 'idle' ? 'Chờ lệnh' : dvrInfo.status === 'running' ? 'Đang quét' : dvrInfo.status}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {dvrInfo.status === 'running' 
                ? `Tiến độ: ${dvrInfo.progress}/${dvrInfo.total}` 
                : 'Không có tác vụ nền'}
            </div>
          </div>
        </div>

        {/* Card 4: Zalo Security Monitor */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Zalo Monitor</span>
            <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-500">
              <MessageSquare size={16} />
            </div>
          </div>
          <div>
            <div className="text-xl font-black text-slate-900 dark:text-white flex items-center gap-1.5">
              <span>{zaloInfo.isMonitoring ? 'Đang chạy' : 'Tạm dừng'}</span>
              {zaloInfo.isMonitoring && <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              <span>Tin: {zaloInfo.totalDetected}</span>
              <span className="mx-1">•</span>
              <span>Đã sync: {zaloInfo.totalSynced}</span>
            </div>
          </div>
        </div>
      </div>

      {/* === QUICK ACCESS MODULE GRID === */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Các phân hệ kiểm tra & vận hành
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Module 1: Check Camera */}
          <div 
            onClick={() => navigate('/admin/camera')}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-blue-500 dark:hover:border-blue-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
                <Camera size={20} strokeWidth={2.3} />
              </div>
              <div>
                <h4 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  Check Camera & FTEL DVR
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  Kiểm tra trực tuyến camera IP và đầu ghi DVR định kỳ theo danh sách kho, xuất file đối soát và đồng bộ Google Sheets.
                </p>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-bold text-blue-600 dark:text-blue-400">
              <span>Vào module</span>
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Module 2: Ticket SSC */}
          <div 
            onClick={() => navigate('/admin/ticket')}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-indigo-500 dark:hover:border-indigo-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold">
                <Ticket size={20} strokeWidth={2.3} />
              </div>
              <div>
                <h4 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                  Ticket SSC Automation
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  Phân tích lỗi mất kết nối, gom nhóm theo khu vực cửa hàng và hỗ trợ quản lý quy trình tạo Ticket SSC tự động.
                </p>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-bold text-indigo-600 dark:text-indigo-400">
              <span>Vào module</span>
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Module 3: Motion Analytics */}
          <div 
            onClick={() => navigate('/admin/motion')}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-500 dark:hover:border-teal-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
                <Activity size={20} strokeWidth={2.3} />
              </div>
              <div>
                <h4 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
                  Motion Analytics
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  Phân tích chuyển động AI, phát hiện sự hiện diện theo vùng ROI và hỗ trợ giám sát video độ trễ thấp.
                </p>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-bold text-teal-600 dark:text-teal-400">
              <span>Vào module</span>
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Module 4: Zalo Monitor */}
          <div 
            onClick={() => navigate('/admin/zalo')}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-rose-500 dark:hover:border-rose-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center font-bold">
                <MessageSquare size={20} strokeWidth={2.3} />
              </div>
              <div>
                <h4 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-rose-600 dark:group-hover:text-rose-400 transition-colors">
                  Zalo Security Monitor
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  Giám sát nhóm an ninh Zalo, nhận diện cảnh báo sự cố, gom luồng phản hồi và đồng bộ tự động lên Google Sheets.
                </p>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-bold text-rose-600 dark:text-rose-400">
              <span>Vào module</span>
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Module 5: Test Settings */}
          <div 
            onClick={() => navigate('/admin/settings')}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-violet-500 dark:hover:border-violet-500/50 transition-all shadow-xs hover:shadow-md cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-violet-500/10 text-violet-600 dark:text-violet-400 flex items-center justify-center font-bold">
                <Sliders size={20} strokeWidth={2.3} />
              </div>
              <div>
                <h4 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                  Cài đặt Hệ thống Test
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  Cấu hình đường dẫn file kho, tài khoản Google Sheets, chu kỳ quét tự động và các tham số kỹ thuật.
                </p>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-bold text-violet-600 dark:text-violet-400">
              <span>Vào module</span>
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Module 6: System Admin (DashboardD Backend) */}
          <div 
            onClick={() => navigate('/admin/system')}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-amber-200 dark:border-amber-900/60 hover:border-amber-500 transition-all shadow-xs hover:shadow-md cursor-pointer group flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center font-bold">
                <Server size={20} strokeWidth={2.3} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors">
                    Quản trị Hệ thống Dashboard
                  </h4>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300">
                    Bảo mật
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  Lịch tự động đồng bộ Auto-Sync 3 chuỗi, cấu hình TOTP 2FA, nhật ký server 8000 và quản trị database.
                </p>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-bold text-amber-600 dark:text-amber-400">
              <span>Đăng nhập Admin Dashboard</span>
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="text-center pt-4 text-xs text-slate-400 dark:text-slate-500 flex items-center justify-center gap-2">
        <Clock size={13} />
        <span>Cập nhật trạng thái gần nhất: {lastCheckTime || '---'}</span>
      </div>
    </div>
  );
};
