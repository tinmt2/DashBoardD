import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { 
  Activity, LayoutDashboard, Map, Users, ShieldAlert, Settings, Bell, Palette, 
  Save, X, Store, Pill, ShieldPlus, BarChart3, Users2, ChevronLeft, ChevronRight,
  CheckCircle2, AlertCircle, Eye, EyeOff, Menu, RefreshCw
} from 'lucide-react';
import TitleBar from './TitleBar';
import { getFptShopAuthStatus, startFptShopAuth } from '../../services/fptShopApi';
import { useNotification } from '../../context/NotificationContext';
import { useSync } from '../../context/SyncContext';
import { RealtimeSyncBanner, CircularSpinner } from '../common/CircularSpinner';
import NotificationPanel from './NotificationPanel';
import BrandLogo from '../common/BrandLogo';

export interface SidebarContextType {
  isCollapsed: boolean;
  toggleSidebar: () => void;
}

export const SidebarContext = React.createContext<SidebarContextType>({
  isCollapsed: false,
  toggleSidebar: () => {}
});

export const useSidebar = () => React.useContext(SidebarContext);

const Layout: React.FC = () => {
  const { unreadCount, togglePanel } = useNotification();
  const { isSyncing, syncStepText, syncDuration, syncToast, setSyncToast, syncAll, syncChain } = useSync();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [fptCreds, setFptCreds] = useState({ username: '', password: '' });
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem('sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });

  const [isHovered, setIsHovered] = useState(false);
  const hoverTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }
    if (isCollapsed) {
      setIsHovered(true);
    }
  };

  const handleMouseLeave = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    hoverTimeoutRef.current = setTimeout(() => {
      setIsHovered(false);
    }, 200);
  };

  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  const toggleSidebar = () => {
    setIsCollapsed(prev => {
      const next = !prev;
      try {
        localStorage.setItem('sidebar_collapsed', String(next));
      } catch {}
      return next;
    });
    setIsHovered(false);
  };

  const effectiveCollapsed = isCollapsed && !isHovered;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        toggleSidebar();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem('fptCreds');
    let creds = { username: '', password: '' };
    if (saved) {
      try {
        creds = JSON.parse(saved);
        setFptCreds(creds);
      } catch (e) {}
    }

    // Automatically check FPT Shop login status in background when web opens
    getFptShopAuthStatus().then(res => {
      if (!res.authenticated && res.status === 'STOPPED') {
        startFptShopAuth(creds).catch(() => {});
      }
    }).catch(() => {});
  }, []);

  const saveSettings = () => {
    localStorage.setItem('fptCreds', JSON.stringify(fptCreds));
    setIsSettingsOpen(false);
  };

  const location = useLocation();

  useEffect(() => {
    setIsMobileOpen(false);
  }, [location.pathname]);

  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/' || path === '/dashboard') return 'Tổng quan';
    if (path.includes('fpt-shop')) return 'FPT Shop';
    if (path.includes('long-chau')) return 'Long Châu';
    if (path.includes('vaccine')) return 'Vaccine';
    if (path.includes('employees')) return 'Quản lý nhân viên';
    if (path.includes('analytics')) return 'Analytics';
    return 'DashBoardD';
  };

  const handleMobileSync = () => {
    const path = location.pathname;
    if (path.includes('fpt-shop')) {
      syncChain('FPT Shop');
    } else if (path.includes('long-chau')) {
      syncChain('Long Châu');
    } else if (path.includes('vaccine')) {
      syncChain('Vaccine');
    } else {
      syncAll();
    }
  };
  // Active and hover styling for navigation links with per-chain theme accents
  const getNavItemClass = (isActive: boolean, theme: 'indigo' | 'rose' | 'blue' | 'teal' | 'violet') => {
    const activeThemes = {
      indigo: 'bg-indigo-50/90 text-indigo-700 font-bold border-indigo-100/90 shadow-[0_1px_4px_rgba(99,102,241,0.08)]',
      rose: 'bg-rose-50/90 text-rose-700 font-bold border-rose-100/90 shadow-[0_1px_4px_rgba(244,63,94,0.08)]',
      blue: 'bg-blue-50/90 text-blue-700 font-bold border-blue-100/90 shadow-[0_1px_4px_rgba(37,99,235,0.08)]',
      teal: 'bg-teal-50/90 text-teal-700 font-bold border-teal-100/90 shadow-[0_1px_4px_rgba(20,184,166,0.08)]',
      violet: 'bg-violet-50/90 text-violet-700 font-bold border-violet-100/90 shadow-[0_1px_4px_rgba(139,92,246,0.08)]',
    };

    const indicatorThemes = {
      indigo: 'bg-gradient-to-b from-indigo-500 to-blue-600 shadow-[0_0_8px_rgba(99,102,241,0.6)]',
      rose: 'bg-gradient-to-b from-rose-500 to-pink-600 shadow-[0_0_8px_rgba(244,63,94,0.6)]',
      blue: 'bg-gradient-to-b from-blue-500 to-indigo-600 shadow-[0_0_8px_rgba(37,99,235,0.6)]',
      teal: 'bg-gradient-to-b from-teal-500 to-emerald-600 shadow-[0_0_8px_rgba(20,184,166,0.6)]',
      violet: 'bg-gradient-to-b from-violet-500 to-purple-600 shadow-[0_0_8px_rgba(139,92,246,0.6)]',
    };

    const iconThemes = {
      indigo: 'text-indigo-600',
      rose: 'text-rose-600',
      blue: 'text-blue-600',
      teal: 'text-teal-600',
      violet: 'text-violet-600',
    };

    return {
      linkClass: `group relative rounded-xl text-[13px] font-semibold transition-all duration-200 flex items-center border border-transparent ${
        effectiveCollapsed ? 'justify-center w-10 h-10 mx-auto' : 'px-3 py-2 gap-2.5 w-full'
      } ${
        isActive
          ? activeThemes[theme]
          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
      }`,
      indicatorClass: indicatorThemes[theme],
      iconClass: isActive ? iconThemes[theme] : 'text-slate-400 group-hover:text-slate-700 group-hover:scale-110 transition-all'
    };
  };

  return (
    <SidebarContext.Provider value={{ isCollapsed: effectiveCollapsed, toggleSidebar }}>
      <div className="flex flex-col h-screen text-slate-800 overflow-hidden font-sans relative">
        
        {/* Global Dynamic Background - Aurora Blue */}
        <div 
          className="absolute inset-0 z-0 transition-all duration-1000"
          style={{
            backgroundColor: '#f0f9ff',
            backgroundImage: 'radial-gradient(circle at 0% 0%, rgba(14, 165, 233, 0.25), transparent 50%), radial-gradient(circle at 100% 100%, rgba(99, 102, 241, 0.2), transparent 50%), radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.15), transparent 60%)',
            filter: 'blur(30px)',
            transform: 'scale(1.1)'
          }}
        />

        <TitleBar />

        <div className="flex flex-1 overflow-hidden relative z-10">
          
          {/* Mobile Backdrop Overlay */}
          {isMobileOpen && (
            <div 
              className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 md:hidden animate-fade-in"
              onClick={() => setIsMobileOpen(false)}
            />
          )}

          {/* === Sidebar Navigation === */}
          <aside 
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            className={`
              fixed inset-y-0 left-0 z-50 w-[270px] p-3.5 bg-white/95 backdrop-blur-2xl shadow-2xl transition-transform duration-300 ease-in-out select-none flex flex-col justify-between
              ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}
              md:relative md:inset-auto md:translate-x-0 md:bg-white/75 md:backdrop-blur-2xl md:border-r md:border-slate-200/60 md:shrink-0
              ${effectiveCollapsed ? 'md:w-[74px] md:px-2 md:py-3.5' : 'md:w-[252px] md:p-3.5'}
              ${isHovered && isCollapsed ? 'md:shadow-[8px_0_32px_rgba(0,0,0,0.08)]' : 'md:shadow-[4px_0_24px_rgba(0,0,0,0.02)]'}
            `}
          >
            <div className="flex flex-col gap-1.5">
              {/* Mobile Drawer Header with Close Button */}
              <div className="flex items-center justify-between pb-3 pt-1 border-b border-slate-200/60 md:hidden">
                <div className="flex items-center gap-2 pl-1">
                  <BrandLogo size={24} className="rounded-md shadow-2xs shrink-0" />
                  <span className="font-bold text-slate-800 text-[15px]">DashBoardD</span>
                </div>
                <button 
                  type="button" 
                  onClick={() => setIsMobileOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                  aria-label="Đóng menu"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Modern Inset Toggle Switch (Aligned to the left - sát bên trái, Desktop only) */}
              <div className={`hidden md:flex items-center pb-2.5 pt-0.5 border-b border-slate-200/60 w-full transition-all ${
                effectiveCollapsed ? 'justify-center' : 'justify-start pl-1'
              }`}>
                <button
                  type="button"
                  role="switch"
                  aria-checked={!isCollapsed}
                  onClick={toggleSidebar}
                  className={`group relative inline-flex h-6 w-12 shrink-0 cursor-pointer items-center rounded-full p-0.5 transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500/30 hover:scale-[1.03] active:scale-95 shadow-inner ${
                    !isCollapsed
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 shadow-[0_2px_8px_rgba(79,70,229,0.35)]'
                      : 'bg-slate-200 hover:bg-slate-300 border border-slate-300/60'
                  }`}
                  title={!isCollapsed ? "Thanh bên đang BẬT - Nhấn để TẮT / Thu gọn (Ctrl+B)" : "Thanh bên đang TẮT - Nhấn để BẬT / Ghim mở (Ctrl+B)"}
                >
                  {/* Background state glyphs (I for ON, O for OFF) */}
                  <span className="sr-only">Bật / Tắt thanh bên</span>
                  <span 
                    aria-hidden="true" 
                    className={`absolute left-1.5 text-[9px] font-black text-white/90 select-none transition-opacity duration-200 ${
                      !isCollapsed ? 'opacity-100' : 'opacity-0'
                    }`}
                  >
                    I
                  </span>
                  <span 
                    aria-hidden="true" 
                    className={`absolute right-1.5 text-[9px] font-bold text-slate-400 select-none transition-opacity duration-200 ${
                      !isCollapsed ? 'opacity-0' : 'opacity-100'
                    }`}
                  >
                    O
                  </span>

                  {/* Sliding Thumb Knob */}
                  <span
                    aria-hidden="true"
                    className={`pointer-events-none inline-flex h-5 w-5 transform items-center justify-center rounded-full bg-white shadow-[0_2px_4px_rgba(0,0,0,0.22)] transition-transform duration-250 ease-out ${
                      !isCollapsed ? 'translate-x-6' : 'translate-x-0'
                    }`}
                  >
                    <span
                      className={`rounded-full transition-colors duration-200 ${
                        !isCollapsed
                          ? 'h-2 w-2 bg-indigo-600'
                          : 'h-1.5 w-1.5 bg-slate-300'
                      }`}
                    />
                  </span>
                </button>
              </div>

              {/* Actions Container in Sidebar (Date filter & Sync button) */}
              <div className="pb-1 min-h-[68px] flex items-center justify-center relative z-40">
                <div id="sidebar-actions" className="w-full relative z-40"></div>
              </div>
              
              {/* Menu Items */}
              <div className="flex flex-col gap-1">
                <NavLink to="/dashboard" title="Tổng quan">
                  {({ isActive }) => {
                    const { linkClass, indicatorClass, iconClass } = getNavItemClass(isActive, 'indigo');
                    return (
                      <div className={linkClass}>
                        <BarChart3 size={17} strokeWidth={2.3} className={`shrink-0 ${iconClass}`} />
                        {!effectiveCollapsed && <span className="truncate">Tổng quan</span>}
                        {isActive && (
                          <span className={`absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full ${indicatorClass}`} />
                        )}
                      </div>
                    );
                  }}
                </NavLink>

                {/* Group 2: Chuỗi hệ thống */}
                {!effectiveCollapsed ? (
                  <div className="pt-3 pb-1 px-3">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 select-none">
                      Chuỗi hệ thống
                    </span>
                  </div>
                ) : (
                  <div className="w-6 h-px bg-slate-200/60 mx-auto my-1.5" />
                )}

                <NavLink to="/fpt-shop" title="FPT Shop">
                  {({ isActive }) => {
                    const { linkClass, indicatorClass, iconClass } = getNavItemClass(isActive, 'rose');
                    return (
                      <div className={linkClass}>
                        <Store size={17} strokeWidth={2.3} className={`shrink-0 ${iconClass}`} />
                        {!effectiveCollapsed && <span className="truncate">FPT Shop</span>}
                        {isActive && (
                          <span className={`absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full ${indicatorClass}`} />
                        )}
                      </div>
                    );
                  }}
                </NavLink>

                <NavLink to="/long-chau" title="Long Châu">
                  {({ isActive }) => {
                    const { linkClass, indicatorClass, iconClass } = getNavItemClass(isActive, 'blue');
                    return (
                      <div className={linkClass}>
                        <Pill size={17} strokeWidth={2.3} className={`shrink-0 ${iconClass}`} />
                        {!effectiveCollapsed && <span className="truncate">Long Châu</span>}
                        {isActive && (
                          <span className={`absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full ${indicatorClass}`} />
                        )}
                      </div>
                    );
                  }}
                </NavLink>

                <NavLink to="/vaccine" title="Vaccine">
                  {({ isActive }) => {
                    const { linkClass, indicatorClass, iconClass } = getNavItemClass(isActive, 'teal');
                    return (
                      <div className={linkClass}>
                        <ShieldPlus size={17} strokeWidth={2.3} className={`shrink-0 ${iconClass}`} />
                        {!effectiveCollapsed && <span className="truncate">Vaccine</span>}
                        {isActive && (
                          <span className={`absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full ${indicatorClass}`} />
                        )}
                      </div>
                    );
                  }}
                </NavLink>

                {/* Group 3: Quản lý */}
                {!effectiveCollapsed ? (
                  <div className="pt-3 pb-1 px-3">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 select-none">
                      Quản lý
                    </span>
                  </div>
                ) : (
                  <div className="w-6 h-px bg-slate-200/60 mx-auto my-1.5" />
                )}

                <NavLink to="/employees" title="Nhân sự">
                  {({ isActive }) => {
                    const { linkClass, indicatorClass, iconClass } = getNavItemClass(isActive, 'violet');
                    return (
                      <div className={linkClass}>
                        <Users2 size={17} strokeWidth={2.3} className={`shrink-0 ${iconClass}`} />
                        {!effectiveCollapsed && <span className="truncate">Nhân sự</span>}
                        {isActive && (
                          <span className={`absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full ${indicatorClass}`} />
                        )}
                      </div>
                    );
                  }}
                </NavLink>
              </div>
            </div>

            {/* Bottom Utilities */}
            <div className="flex flex-col gap-1 pt-2.5 border-t border-slate-200/60">
              {!effectiveCollapsed && (
                <div className="px-3 pb-0.5">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 select-none">
                    Hệ thống
                  </span>
                </div>
              )}

              <button 
                type="button"
                onClick={togglePanel}
                className={`group flex items-center rounded-xl text-[13px] font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-all cursor-pointer relative ${
                  effectiveCollapsed ? 'justify-center w-10 h-10 mx-auto' : 'px-3 py-2 justify-between w-full'
                }`}
                title="Thông báo đồng bộ"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="relative flex items-center justify-center">
                    <Bell size={17} strokeWidth={2.3} className="text-slate-400 group-hover:text-slate-700 group-hover:scale-110 transition-all shrink-0" />
                    {unreadCount > 0 && effectiveCollapsed && (
                      <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-rose-500 rounded-full ring-2 ring-white animate-pulse" />
                    )}
                  </div>
                  {!effectiveCollapsed && <span className="truncate">Thông báo</span>}
                </div>
                {!effectiveCollapsed && (
                  unreadCount > 0 ? (
                    <span className="px-1.5 py-0.5 text-[10.5px] font-bold rounded-full bg-rose-500 text-white shadow-sm shadow-rose-500/30 animate-pulse">
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
                  )
                )}
              </button>

              <button 
                type="button"
                onClick={() => setIsSettingsOpen(true)} 
                className={`group flex items-center rounded-xl text-[13px] font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100/70 transition-all cursor-pointer ${
                  effectiveCollapsed ? 'justify-center w-10 h-10 mx-auto' : 'px-3 py-2 gap-2.5 w-full text-left'
                }`}
                title="Inside"
              >
                <Settings size={17} strokeWidth={2.3} className="text-slate-400 group-hover:text-slate-700 group-hover:scale-110 transition-all shrink-0" />
                {!effectiveCollapsed && <span className="truncate">Inside</span>}
              </button>
              
              {/* Last updated container at the bottom of the sidebar */}
              <div id="sidebar-footer-time" className={`${effectiveCollapsed ? 'p-1 flex justify-center' : 'pt-2'} mt-0.5`}></div>
            </div>
          </aside>

        {/* === Main Content Area === */}
        <div className="flex-1 flex flex-col min-w-0 relative z-10 overflow-hidden">
          
          {/* Mobile Top Header (Visible on screens < md) */}
          <header className="md:hidden h-14 px-4 bg-white/80 backdrop-blur-xl border-b border-slate-200/60 flex items-center justify-between shrink-0 z-30">
            <div className="flex items-center gap-2.5">
              <button 
                type="button" 
                onClick={() => setIsMobileOpen(true)}
                className="p-2 -ml-1 rounded-xl text-slate-700 hover:text-slate-900 hover:bg-slate-100 active:scale-95 transition-all cursor-pointer"
                title="Mở menu điều hướng"
                aria-label="Mở menu điều hướng"
              >
                <Menu size={20} strokeWidth={2.4} />
              </button>
              <div className="flex items-center gap-2">
                <BrandLogo size={22} className="rounded-md shadow-2xs shrink-0" />
                <span className="font-bold text-[15px] text-slate-800 tracking-tight">{getPageTitle()}</span>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {/* Quick Sync Button on Mobile Header */}
              <button 
                type="button" 
                onClick={handleMobileSync} 
                disabled={isSyncing}
                className={`p-2 rounded-xl transition-all cursor-pointer ${
                  isSyncing 
                    ? "bg-slate-900 text-emerald-400 ring-2 ring-emerald-500/20" 
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100 active:scale-95"
                }`}
                title={isSyncing ? `${syncStepText} (${syncDuration}s)` : "Đồng bộ dữ liệu"}
                aria-label="Đồng bộ dữ liệu"
              >
                {isSyncing ? (
                  <div className="flex items-center gap-1 px-1">
                    <CircularSpinner size={15} className="text-emerald-400 shrink-0" />
                    <span className="text-[10.5px] font-bold tabular-nums text-emerald-400">{syncDuration}s</span>
                  </div>
                ) : (
                  <RefreshCw size={17} strokeWidth={2.3} />
                )}
              </button>

              <button 
                type="button" 
                onClick={togglePanel} 
                className="relative p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
                title="Thông báo"
              >
                <Bell size={18} />
                {unreadCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white"></span>
                )}
              </button>
              <button 
                type="button"
                onClick={() => setIsSettingsOpen(true)}
                className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
                title="Inside"
              >
                <Settings size={18} />
              </button>
            </div>
          </header>

          {/* Minimal Top Header for page actions on desktop */}
          <header className="hidden md:flex absolute top-0 right-0 w-full items-center justify-end p-8 z-40 pointer-events-none">
            <div id="topbar-actions" className="flex items-center gap-2 pointer-events-auto"></div>
          </header>

          <main className="flex-1 min-w-0 relative z-10 flex flex-col overflow-y-auto">
            <div key={location.pathname} className="flex-1 flex flex-col min-w-0 animate-page-glide">
              <Outlet />
            </div>
            
            {isSettingsOpen && createPortal(
              <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
                <div className="bg-white rounded-xl shadow-xl w-[400px] max-w-[90vw] overflow-hidden">
                  <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50">
                    <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                      <Settings size={18} className="text-indigo-600" /> Cài đặt Tài khoản Inside
                    </h3>
                    <button onClick={() => setIsSettingsOpen(false)} className="text-slate-400 hover:text-rose-500 transition-colors">
                      <X size={20} />
                    </button>
                  </div>
                  <div className="p-5 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Tài khoản (Username)</label>
                      <input 
                        type="text" 
                        value={fptCreds.username} 
                        onChange={e => setFptCreds({...fptCreds, username: e.target.value})} 
                        className="w-full px-3 py-2 bg-white text-slate-900 placeholder:text-slate-400 font-medium border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm" 
                        placeholder="Nhập tên đăng nhập" 
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Mật khẩu (Password)</label>
                      <div className="relative flex items-center">
                        <input 
                          type={showPassword ? "text" : "password"} 
                          value={fptCreds.password} 
                          onChange={e => setFptCreds({...fptCreds, password: e.target.value})} 
                          className="w-full px-3 py-2 pr-10 bg-white text-slate-900 placeholder:text-slate-400 font-medium border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm" 
                          placeholder="Nhập mật khẩu" 
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(prev => !prev)}
                          className="absolute right-2.5 text-slate-400 hover:text-slate-600 p-1 cursor-pointer transition-colors"
                          title={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                        >
                          {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="p-4 border-t border-slate-100 flex justify-end gap-2 bg-slate-50">
                    <button onClick={() => setIsSettingsOpen(false)} className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">Hủy</button>
                    <button onClick={saveSettings} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors flex items-center gap-2"><Save size={16} /> Lưu cài đặt</button>
                  </div>
                </div>
              </div>,
              document.body
            )}
            <NotificationPanel />

            {/* Global Realtime Sync Status Banner */}
            <RealtimeSyncBanner 
              isSyncing={isSyncing} 
              statusText={syncStepText} 
              duration={syncDuration} 
            />

            {/* Global Sync Toast Notification */}
            {syncToast?.show && createPortal(
              <div className={`fixed top-6 right-6 bg-white/95 backdrop-blur-md border ${
                syncToast.type === 'success' ? 'border-emerald-200/80' : syncToast.type === 'warning' ? 'border-amber-200/80' : 'border-rose-200/80'
              } rounded-2xl p-4 shadow-[0_10px_35px_rgba(0,0,0,0.1)] flex items-center gap-3.5 z-[9999] animate-toast-pop`}>
                <div className={`w-10 h-10 rounded-full ${
                  syncToast.type === 'success' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : syncToast.type === 'warning' ? 'bg-amber-50 text-amber-600 border-amber-100' : 'bg-rose-50 text-rose-600 border-rose-100'
                } flex items-center justify-center text-lg shrink-0 border animate-icon-bounce`}>
                  {syncToast.type === 'success' ? <CheckCircle2 size={22} /> : <AlertCircle size={22} />}
                </div>
                <div className="max-w-md">
                  <div className="text-[14px] font-bold text-slate-800">{syncToast.title}</div>
                  {syncToast.subtitle && (
                    <div className="text-[12px] font-medium text-slate-500 mt-0.5 leading-snug">{syncToast.subtitle}</div>
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
          </main>
        </div>

      </div>
    </div>
  </SidebarContext.Provider>
  );
};

export default Layout;