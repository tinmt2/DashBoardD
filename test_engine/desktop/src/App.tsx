import React, { useEffect, useState } from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import { LayoutDashboard, Camera, Ticket, Activity, Settings as SettingsIcon, AlertCircle, CheckCircle, Loader2, MessageSquare, RefreshCw } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import CheckCamera from './pages/CheckCamera';
import AllShop from './pages/AllShop';
import TicketSSC from './pages/TicketSSC';
import MotionAnalytics from './pages/MotionAnalytics';
import Settings from './pages/Settings';
import ZaloMonitor from './pages/ZaloMonitor';
import { healthApi } from './api';
import { TitleBar } from './components/TitleBar';
import { useTaskContext } from './context/TaskContext';
import { logger } from './utils/logger';

const App: React.FC = () => {
  const [isReloading, setIsReloading] = useState(false);

  const handleReloadApp = async () => {
    setIsReloading(true);
    try {
      if (window.electronAPI?.invoke) {
        await window.electronAPI.invoke('restart-app');
      } else {
        window.location.reload();
      }
    } catch (e) {
      console.error('Error restarting:', e);
      window.location.reload();
    } finally {
      setTimeout(() => setIsReloading(false), 2000);
    }
  };

  const { tasks } = useTaskContext();
  const [processStatus, setProcessStatus] = useState('Starting');
  const [processMessage, setProcessMessage] = useState('');
  
  const [apiStatus, setApiStatus] = useState<'Checking' | 'Connected' | 'Disconnected'>('Checking');
  const [apiMessage, setApiMessage] = useState('');
  
  const [userAvatar, setUserAvatar] = useState(localStorage.getItem('userAvatar') || '');

  useEffect(() => {
    logger.info('APP_START', 'Frontend React Application Started');
  }, []);

  useEffect(() => {
    const handleAvatarChange = () => {
      setUserAvatar(localStorage.getItem('userAvatar') || '');
    };
    window.addEventListener('avatarChanged', handleAvatarChange);
    return () => window.removeEventListener('avatarChanged', handleAvatarChange);
  }, []);

  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.onBackendStatus((data: any) => {
        setProcessStatus(data.status);
        if (data.message) setProcessMessage(data.message);
      });
      // Fetch initial state to avoid race condition
      window.electronAPI.invoke('get-backend-status').then((data: any) => {
        if (data) {
          setProcessStatus(data.status);
          if (data.message) setProcessMessage(data.message);
        }
      });
    } else {
      setProcessStatus('Ready');
    }
  }, []);

  // Poll Health API independently
  useEffect(() => {
    if (processStatus !== 'Ready') {
      setApiStatus('Disconnected');
      setApiMessage('Waiting for Process');
      return;
    }

    setApiStatus('Checking');
    const checkHealth = async () => {
      const response = await healthApi.check();
      if (response.success && response.status === 'ok') {
        setApiStatus('Connected');
        setApiMessage('');
      } else {
        setApiStatus('Disconnected');
        setApiMessage(response.message || 'Health check failed');
      }
    };

    checkHealth();
    const intervalId = setInterval(checkHealth, 5000);
    return () => clearInterval(intervalId);
  }, [processStatus]);

  const renderProcessIcon = () => {
    switch(processStatus) {
      case 'Ready': return <CheckCircle className="w-4 h-4 text-green-500 mr-2" />;
      case 'Starting': return <Loader2 className="w-4 h-4 text-blue-500 animate-spin mr-2" />;
      default: return <AlertCircle className="w-4 h-4 text-red-500 mr-2" />;
    }
  };
  
  const renderApiIcon = () => {
    switch(apiStatus) {
      case 'Connected': return <CheckCircle className="w-4 h-4 text-green-500 mr-2" />;
      case 'Checking': return <Loader2 className="w-4 h-4 text-blue-500 animate-spin mr-2" />;
      default: return <AlertCircle className="w-4 h-4 text-red-500 mr-2" />;
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-slate-950">
      <TitleBar />
      <div className="flex-1 overflow-hidden bg-slate-900 rounded-tl-2xl border-t border-l border-slate-800 shadow-inner flex">
        {/* Sidebar */}
        <div className="w-64 bg-slate-950/50 backdrop-blur border-r border-slate-800 text-slate-300 flex flex-col rounded-tl-2xl overflow-hidden">
          <div className="h-24 flex items-center px-6 border-b border-slate-800/60 cursor-pointer hover:bg-slate-800/30 transition-colors group">
            <div className="relative flex items-center justify-center w-11 h-11 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-400 p-[2px] shadow-lg shadow-emerald-500/20 group-hover:shadow-emerald-500/40 transition-shadow">
              <div className="w-full h-full rounded-full bg-slate-950 flex items-center justify-center overflow-hidden">
                {userAvatar ? (
                  <img src={userAvatar} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-emerald-400 font-bold text-lg">T</span>
                )}
              </div>
              <div className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 border-2 border-slate-950 rounded-full"></div>
            </div>
            <div className="flex flex-col ml-4">
              <span className="text-sm font-bold text-white tracking-wide">Tín</span>
              <span className="text-[9px] font-bold tracking-[0.2em] text-emerald-500 uppercase mt-0.5">Administrator</span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto py-6">
            <nav className="space-y-2 px-4">
              <NavLink draggable={false} to="/" className={({ isActive }) => `flex items-center px-4 py-3 rounded-lg transition-all text-[10px] font-bold tracking-[0.15em] uppercase ${isActive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'}`}>
                <LayoutDashboard className="w-4 h-4 mr-4" /> Dashboard
              </NavLink>
              <NavLink draggable={false} to="/check-camera" className={({ isActive }) => `flex items-center justify-between px-4 py-3 rounded-lg transition-all text-[10px] font-bold tracking-[0.15em] uppercase ${isActive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'}`}>
                <div className="flex items-center"><Camera className="w-4 h-4 mr-4" /> Check Camera</div>
                {tasks['camera'] && (tasks['camera'].status === 'running' || tasks['camera'].status === 'queued') && (
                  <span className="text-emerald-400 font-mono text-[9px] animate-pulse">
                    {tasks['camera'].total > 0 ? `[${Math.round((tasks['camera'].progress / tasks['camera'].total) * 100)}%]` : '[●]'}
                  </span>
                )}
              </NavLink>
                            <NavLink draggable={false} to="/all-shop" className={({ isActive }) => `flex items-center justify-between px-4 py-3 rounded-lg transition-all text-[10px] font-bold tracking-[0.15em] uppercase ${isActive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'}`}>
                <div className="flex items-center"><LayoutDashboard className="w-4 h-4 mr-4" /> All Shop</div>
              </NavLink>
              <NavLink draggable={false} to="/ticket" className={({ isActive }) => `flex items-center justify-between px-4 py-3 rounded-lg transition-all text-[10px] font-bold tracking-[0.15em] uppercase ${isActive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'}`}>
                <div className="flex items-center"><Ticket className="w-4 h-4 mr-4" /> Ticket SSC</div>
                {tasks['ticket'] && (tasks['ticket'].status === 'running' || tasks['ticket'].status === 'queued') && (
                  <span className="text-emerald-400 font-mono text-[9px] animate-pulse">
                    {tasks['ticket'].total > 0 ? `[${Math.round((tasks['ticket'].progress / tasks['ticket'].total) * 100)}%]` : '[●]'}
                  </span>
                )}
              </NavLink>
              <NavLink draggable={false} to="/motion" className={({ isActive }) => `flex items-center justify-between px-4 py-3 rounded-lg transition-all text-[10px] font-bold tracking-[0.15em] uppercase ${isActive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'}`}>
                <div className="flex items-center"><Activity className="w-4 h-4 mr-4" /> Motion</div>
                {tasks['motion'] && (tasks['motion'].status === 'running' || tasks['motion'].status === 'queued') && (
                  <span className="text-emerald-400 font-mono text-[9px] animate-pulse">
                    {tasks['motion'].total > 0 ? `[${Math.round((tasks['motion'].progress / tasks['motion'].total) * 100)}%]` : '[●]'}
                  </span>
                )}
              </NavLink>
              <NavLink draggable={false} to="/zalo-monitor" className={({ isActive }) => `flex items-center px-4 py-3 rounded-lg transition-all text-[10px] font-bold tracking-[0.15em] uppercase ${isActive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'}`}>
                <MessageSquare className="w-4 h-4 mr-4" /> Zalo Monitor
              </NavLink>
              <NavLink draggable={false} to="/settings"  className={({ isActive }) => `flex items-center px-4 py-3 rounded-lg transition-all text-[10px] font-bold tracking-[0.15em] uppercase ${isActive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'}`}>
                <SettingsIcon className="w-4 h-4 mr-4" /> Settings
              </NavLink>
            </nav>
          </div>
          {/* Quick Reload Bar */}
          <div className="p-3 border-t border-slate-800/80 bg-slate-950/40">
            <button
              onClick={handleReloadApp}
              disabled={isReloading}
              title="Khởi động lại Backend Python và làm mới giao diện"
              className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-emerald-400 border border-slate-700/60 hover:border-emerald-500/30 transition-all text-[10px] font-bold tracking-[0.15em] uppercase group disabled:opacity-50 cursor-pointer shadow-sm"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-400 group-hover:text-emerald-400 transition-colors ${isReloading ? 'animate-spin text-emerald-400' : ''}`} />
              <span>{isReloading ? 'Đang khởi động...' : 'Reload App & Backend'}</span>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {/* No global header needed anymore */}

          {/* Page Content */}
          <main className="flex-1 overflow-y-auto bg-slate-950">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/check-camera" element={<CheckCamera />} />
              <Route path="/all-shop" element={<AllShop />} />
              <Route path="/ticket" element={<TicketSSC />} />
              <Route path="/motion" element={<MotionAnalytics />} />
              <Route path="/zalo-monitor" element={<ZaloMonitor />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>

          {/* Footer / Status */}
          <footer className="h-10 bg-slate-950 border-t border-slate-800 flex items-center justify-between px-6 text-sm text-slate-400 font-medium">
            <div className="flex items-center">
              {renderProcessIcon()}
              {processStatus !== 'Ready' && (
                <span className="ml-1">Process: {processStatus} {processMessage && `(${processMessage})`}</span>
              )}
            </div>
            <div className="flex items-center">
              {renderApiIcon()}
              {apiStatus !== 'Connected' && (
                <span className="ml-1">API: {apiStatus} {apiMessage && `(${apiMessage})`}</span>
              )}
            </div>
          </footer>

          {/* Blocking Overlay if Process is not Ready */}
          {processStatus !== 'Ready' && (
            <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
              {processStatus === 'Starting' && (
                <>
                  <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                  <h2 className="text-xl font-semibold text-gray-800">Starting Backend...</h2>
                  <p className="text-gray-500 mt-2">{processMessage || 'Waiting for FastAPI to become ready...'}</p>
                </>
              )}
              {(processStatus === 'Error' || processStatus === 'PortConflict' || processStatus === 'Timeout' || processStatus === 'Stopped') && (
                <>
                  <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
                  <h2 className="text-xl font-semibold text-gray-800">Backend Unavailable</h2>
                  <p className="text-red-600 mt-2">{processMessage || 'Failed to connect to Python backend.'}</p>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
