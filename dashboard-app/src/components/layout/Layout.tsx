import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Activity, LayoutDashboard, Map, Users, ShieldAlert, Settings, Bell, Palette, Save, X } from 'lucide-react';
import TitleBar from './TitleBar';

const Layout: React.FC = () => {
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

  const location = useLocation();

  // Active state styling for navigation links
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-1.5 rounded-full text-[13px] font-bold transition-all duration-300 flex items-center gap-0 ${
      isActive
        ? 'bg-white text-blue-600 shadow-sm shadow-black/5'
        : 'text-slate-600 hover:text-slate-900 hover:bg-white/40'
    }`;

  return (
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

      <div className="flex flex-col flex-1 overflow-hidden relative z-10">
        
        {/* === Top Navigation Bar (Glassmorphism) === */}
        <header className="h-[64px] shrink-0 w-full bg-white/50 backdrop-blur-2xl border-b border-white/60 shadow-[0_4px_16px_rgba(0,0,0,0.02)] flex items-center justify-between px-6 z-50">
          
          {/* Middle: Main Menu Links */}
          <div className="flex items-center gap-1 bg-black/5 p-1 rounded-full mx-4 overflow-x-auto no-scrollbar">
            <NavLink to="/dashboard" className={navLinkClass}>
              Tổng quan
            </NavLink>
            
            <div className="w-px h-4 bg-black/10 mx-1"></div>
            
            <NavLink to="/fpt-shop" className={navLinkClass}>
              FPT Shop
            </NavLink>
            <NavLink to="/long-chau" className={navLinkClass}>
              Long Châu
            </NavLink>
            <NavLink to="/vaccine" className={navLinkClass}>
              Vaccine
            </NavLink>
            
            <div className="w-px h-4 bg-black/10 mx-1"></div>
            
            <NavLink to="/employees" className={navLinkClass}>
              Nhân sự
            </NavLink>
          </div>

          {/* Right side: Design Lab & User Icons */}
          <div className="flex items-center gap-3">
            
            {/* Teleport target for page-specific actions */}
            <div id="topbar-actions" className="flex items-center gap-2"></div>
            
            <div className="w-px h-5 bg-black/10 mx-1"></div>
            
            {/* System Icons */}
            <button className="w-8 h-8 rounded-full bg-white/40 text-slate-600 flex items-center justify-center shadow-sm hover:bg-white hover:text-slate-900 transition-all">
              <Bell size={15} strokeWidth={2.5} />
            </button>
            <button onClick={() => setIsSettingsOpen(true)} className="w-8 h-8 rounded-full bg-white/40 text-slate-600 flex items-center justify-center shadow-sm hover:bg-white hover:text-slate-900 transition-all">
              <Settings size={15} strokeWidth={2.5} />
            </button>

            
          </div>

        </header>

        {/* === Main Content Area === */}
        {/* Set overflow-y-auto here so the outlet controls its own scrolling, 
            or let the outlet scroll if it's full height. */}
        <main className="flex-1 min-w-0 relative z-10 flex flex-col overflow-y-auto">
          <Outlet />
      {isSettingsOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center" style={{zIndex: 9999}}>
          <div className="bg-white rounded-xl shadow-xl w-[400px] max-w-[90vw] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <Settings size={18} className="text-indigo-600" /> Cài đặt Tài khoản FPT Shop
              </h3>
              <button onClick={() => setIsSettingsOpen(false)} className="text-slate-400 hover:text-rose-500 transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Tài khoản (Username)</label>
                <input type="text" value={fptCreds.username} onChange={e => setFptCreds({...fptCreds, username: e.target.value})} className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm" placeholder="Nhập tên đăng nhập" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Mật khẩu (Password)</label>
                <input type="password" value={fptCreds.password} onChange={e => setFptCreds({...fptCreds, password: e.target.value})} className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm" placeholder="Nhập mật khẩu" />
              </div>
              <div className="bg-amber-50 text-amber-700 text-xs p-3 rounded-lg border border-amber-100">
                Lưu ý: Mật khẩu chỉ được lưu trên trình duyệt của bạn (localStorage), không lưu trên server.
              </div>
            </div>
            <div className="p-4 border-t border-slate-100 flex justify-end gap-2 bg-slate-50">
              <button onClick={() => setIsSettingsOpen(false)} className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">Hủy</button>
              <button onClick={saveSettings} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors flex items-center gap-2"><Save size={16} /> Lưu cài đặt</button>
            </div>
          </div>
        </div>
      )}

        </main>

      </div>
    </div>
  );
};

export default Layout;