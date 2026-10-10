import React, { useState } from 'react';
import { LayoutDashboard, Users, AlertCircle, Map, Settings, Bell, Search, Menu, Server, Shield } from 'lucide-react';

type LayoutTheme = 'integrated' | 'island' | 'dock' | 'topnav' | 'mini' | 'split' | 'spatial';

const NavItem = ({ icon: Icon, label, active = false, theme = 'integrated' }: any) => {
  if (theme === 'dock') {
    return (
      <button className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${active ? 'bg-white/20 text-white shadow-sm' : 'text-slate-700 hover:bg-white/10'}`}>
        <Icon size={22} strokeWidth={2.5} />
      </button>
    );
  }

  if (['mini', 'spatial', 'splitPrimary'].includes(theme)) {
    return (
      <button className={`w-11 h-11 rounded-[12px] flex items-center justify-center transition-all ${active ? 'bg-blue-600 text-white shadow-md' : 'text-slate-600 hover:bg-white/40 hover:text-slate-900'}`} title={label}>
        <Icon size={20} strokeWidth={2.5} />
      </button>
    );
  }

  return (
    <div className={`flex items-center gap-3 px-3 py-2 rounded-[10px] cursor-pointer transition-colors ${active ? (theme === 'integrated' ? 'bg-black/5' : 'bg-white/40 shadow-sm') : 'hover:bg-black/5'}`}>
      <Icon size={18} strokeWidth={2.5} className={active ? 'text-blue-600' : 'text-slate-500'} />
      <span className={`text-[13px] font-bold ${active ? 'text-slate-900' : 'text-slate-600'}`}>{label}</span>
    </div>
  );
};

const MockDashboardContent = () => (
  <div className="flex-1 p-8 overflow-y-auto animate-fade-in w-full h-full">
    <div className="flex justify-between items-center mb-8">
      <h2 className="text-[28px] font-bold text-slate-800 tracking-tight">Tổng quan lỗi</h2>
      <div className="flex gap-2">
        <button className="w-8 h-8 rounded-full bg-white/40 flex items-center justify-center shadow-sm backdrop-blur-md"><Search size={16} /></button>
        <button className="w-8 h-8 rounded-full bg-white/40 flex items-center justify-center shadow-sm backdrop-blur-md"><Bell size={16} /></button>
      </div>
    </div>
    <div className="grid grid-cols-3 gap-6 mb-6">
      {[1, 2, 3].map(i => (
        <div key={i} className="h-32 bg-white/40 backdrop-blur-xl border border-white/60 rounded-[24px] p-5 shadow-[0_8px_32px_rgba(0,0,0,0.04)]">
          <div className="w-8 h-8 bg-black/5 rounded-full mb-3"></div>
          <div className="h-4 w-1/2 bg-black/5 rounded-full mb-2"></div>
          <div className="h-3 w-1/3 bg-black/5 rounded-full"></div>
        </div>
      ))}
    </div>
    <div className="h-64 w-full bg-white/40 backdrop-blur-xl border border-white/60 rounded-[24px] p-5 shadow-[0_8px_32px_rgba(0,0,0,0.04)]">
      <div className="h-4 w-1/4 bg-black/5 rounded-full mb-4"></div>
      <div className="space-y-3">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-8 w-full bg-black/5 rounded-[8px]"></div>
        ))}
      </div>
    </div>
  </div>
);

const LayoutPreview = ({ theme }: { theme: LayoutTheme }) => {
  
  const bgStyle = {
    backgroundColor: '#f0f9ff',
    backgroundImage: 'radial-gradient(circle at 0% 0%, rgba(14, 165, 233, 0.25), transparent 50%), radial-gradient(circle at 100% 100%, rgba(99, 102, 241, 0.2), transparent 50%), radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.15), transparent 60%)',
  };

  return (
    <div className="w-full h-[600px] rounded-[32px] overflow-hidden relative shadow-[0_20px_60px_rgba(0,0,0,0.1)] border border-slate-200" style={bgStyle}>
      
      {/* 1. INTEGRATED MAC OS SIDEBAR */}
      {theme === 'integrated' && (
        <div className="flex h-full w-full">
          <div className="w-[240px] h-full bg-white/20 backdrop-blur-2xl border-r border-white/40 flex flex-col pt-8 pb-4 px-4">
            <div className="flex items-center gap-2 mb-8 px-2">
              <div className="w-6 h-6 rounded-md bg-blue-600"></div>
              <span className="font-bold text-slate-800 tracking-tight">OpsMonitor</span>
            </div>
            <div className="space-y-1 flex-1">
              <NavItem theme="integrated" icon={LayoutDashboard} label="Tổng quan lỗi" active />
              <NavItem theme="integrated" icon={AlertCircle} label="Chi tiết lỗi" />
              <NavItem theme="integrated" icon={Map} label="FPT Shop" />
              <NavItem theme="integrated" icon={Map} label="Long Châu" />
              <NavItem theme="integrated" icon={Users} label="Nhân viên" />
            </div>
          </div>
          <MockDashboardContent />
        </div>
      )}

      {/* 2. ISLAND SIDEBAR */}
      {theme === 'island' && (
        <div className="flex h-full w-full p-6 gap-6">
          <div className="w-[220px] h-full bg-white/60 backdrop-blur-3xl border border-white/80 rounded-[32px] shadow-[0_8px_32px_rgba(0,0,0,0.06)] flex flex-col pt-8 pb-4 px-4">
            <div className="flex justify-center mb-8">
              <div className="w-10 h-10 rounded-xl bg-blue-600 shadow-md"></div>
            </div>
            <div className="space-y-2 flex-1">
              <NavItem theme="island" icon={LayoutDashboard} label="Tổng quan" active />
              <NavItem theme="island" icon={AlertCircle} label="Lỗi" />
              <NavItem theme="island" icon={Map} label="Chuỗi" />
              <NavItem theme="island" icon={Users} label="Nhân sự" />
            </div>
          </div>
          <div className="flex-1 h-full bg-white/30 backdrop-blur-xl border border-white/60 rounded-[32px] overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.04)]">
            <MockDashboardContent />
          </div>
        </div>
      )}

      {/* 3. iPAD OS DOCK */}
      {theme === 'dock' && (
        <div className="flex flex-col h-full w-full relative">
          <MockDashboardContent />
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2">
            <div className="bg-white/40 backdrop-blur-3xl border border-white/60 shadow-[0_16px_40px_rgba(0,0,0,0.1)] rounded-full p-2 flex items-center gap-2">
              <NavItem theme="dock" icon={LayoutDashboard} active />
              <NavItem theme="dock" icon={AlertCircle} />
              <div className="w-px h-8 bg-black/10 mx-1"></div>
              <NavItem theme="dock" icon={Map} />
              <NavItem theme="dock" icon={Users} />
              <div className="w-px h-8 bg-black/10 mx-1"></div>
              <NavItem theme="dock" icon={Settings} />
            </div>
          </div>
        </div>
      )}

      {/* 4. TOP NAVIGATION */}
      {theme === 'topnav' && (
        <div className="flex flex-col h-full w-full">
          <div className="h-[64px] w-full bg-white/50 backdrop-blur-2xl border-b border-white/60 shadow-sm flex items-center justify-between px-8">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-md bg-blue-600"></div>
              <span className="font-bold text-slate-800 tracking-tight text-[16px]">OpsMonitor</span>
            </div>
            <div className="flex items-center gap-1 bg-black/5 p-1 rounded-full">
              <button className="px-5 py-1.5 rounded-full bg-white shadow-sm text-[13px] font-bold text-slate-800">Tổng quan</button>
              <button className="px-5 py-1.5 rounded-full text-[13px] font-bold text-slate-600 hover:text-slate-900">Chi tiết lỗi</button>
              <button className="px-5 py-1.5 rounded-full text-[13px] font-bold text-slate-600 hover:text-slate-900">Nhân sự</button>
            </div>
            <div className="w-8 h-8 rounded-full bg-slate-300"></div>
          </div>
          <MockDashboardContent />
        </div>
      )}

      {/* 5. MINI ICON BAR */}
      {theme === 'mini' && (
        <div className="flex h-full w-full">
          <div className="w-[80px] h-full bg-white/30 backdrop-blur-2xl border-r border-white/50 flex flex-col items-center pt-6 pb-6 gap-4">
            <div className="w-10 h-10 rounded-xl bg-blue-600 shadow-md mb-4 flex items-center justify-center text-white font-bold">OM</div>
            <NavItem theme="mini" icon={LayoutDashboard} label="Tổng quan" active />
            <NavItem theme="mini" icon={AlertCircle} label="Lỗi" />
            <NavItem theme="mini" icon={Map} label="Chuỗi" />
            <NavItem theme="mini" icon={Users} label="Nhân sự" />
            <div className="mt-auto">
              <NavItem theme="mini" icon={Settings} label="Cài đặt" />
            </div>
          </div>
          <MockDashboardContent />
        </div>
      )}

      {/* 6. DUAL COLUMN SPLIT VIEW (macOS Mail/Settings) */}
      {theme === 'split' && (
        <div className="flex h-full w-full">
          {/* Primary Sidebar */}
          <div className="w-[72px] h-full bg-black/5 backdrop-blur-3xl border-r border-black/10 flex flex-col items-center pt-6 pb-6 gap-3 z-20">
            <div className="w-9 h-9 rounded-full bg-blue-600 shadow-md mb-4"></div>
            <NavItem theme="splitPrimary" icon={LayoutDashboard} active />
            <NavItem theme="splitPrimary" icon={Server} />
            <NavItem theme="splitPrimary" icon={Shield} />
            <div className="mt-auto">
              <NavItem theme="splitPrimary" icon={Settings} />
            </div>
          </div>
          {/* Secondary Sidebar */}
          <div className="w-[220px] h-full bg-white/30 backdrop-blur-xl border-r border-white/50 flex flex-col pt-6 pb-4 px-3 z-10">
            <h3 className="text-[12px] font-bold text-slate-500 uppercase tracking-widest px-2 mb-4">Giám sát lỗi</h3>
            <div className="space-y-1">
              <NavItem theme="integrated" icon={AlertCircle} label="Tất cả lỗi" active />
              <NavItem theme="integrated" icon={Map} label="FPT Shop" />
              <NavItem theme="integrated" icon={Map} label="Long Châu" />
              <NavItem theme="integrated" icon={Map} label="Vaccine" />
            </div>
          </div>
          {/* Main */}
          <MockDashboardContent />
        </div>
      )}

      {/* 7. VISION OS SPATIAL (Detached floating windows) */}
      {theme === 'spatial' && (
        <div className="flex h-full w-full items-center justify-center p-8 gap-8">
          {/* Spatial Pill */}
          <div className="w-[76px] bg-white/20 backdrop-blur-3xl border border-white/40 rounded-full shadow-[0_16px_40px_rgba(0,0,0,0.15)] flex flex-col items-center py-6 gap-4">
            <NavItem theme="spatial" icon={LayoutDashboard} active />
            <NavItem theme="spatial" icon={AlertCircle} />
            <NavItem theme="spatial" icon={Map} />
            <NavItem theme="spatial" icon={Users} />
          </div>
          {/* Spatial Main Window */}
          <div className="flex-1 h-full bg-white/40 backdrop-blur-3xl border border-white/60 rounded-[40px] shadow-[0_24px_60px_rgba(0,0,0,0.12)] overflow-hidden">
            <MockDashboardContent />
          </div>
        </div>
      )}

    </div>
  );
};

const NavigationConcepts: React.FC = () => {
  const [theme, setTheme] = useState<LayoutTheme>('integrated');

  return (
    <div className="min-h-screen bg-[#f5f5f7] pb-12 font-sans">
      
      {/* Header Info */}
      <div className="w-full max-w-5xl mx-auto pt-12 pb-8 px-6 text-center">
        <h1 className="text-[32px] font-bold text-slate-900 mb-3 tracking-tight">Apple-Style Navigation Layouts</h1>
        <p className="text-[15px] text-slate-600 max-w-2xl mx-auto">
          Sidebar hiện tại đang bị đục màu và không ăn nhập với giao diện Kính của Dashboard. Dưới đây là 7 cấu trúc điều hướng đỉnh cao nhất của Apple để bạn lựa chọn.
        </p>
      </div>

      {/* Selectors */}
      <div className="flex flex-col items-center justify-center gap-4 mb-10">
        
        {/* Row 1: The Classics */}
        <div className="bg-white/80 backdrop-blur-xl border border-slate-200 shadow-sm rounded-full p-1.5 flex gap-1">
          {[
            { id: 'integrated', label: '🖥️ macOS Integrated' },
            { id: 'split', label: '🗂️ Dual Column (Split)' },
            { id: 'mini', label: '📏 Minimal Icon Bar' },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTheme(t.id as any)}
              className={`px-5 py-2 rounded-full text-[13px] font-bold transition-all duration-300 ${
                theme === t.id ? 'bg-slate-900 text-white shadow-md' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Row 2: The Moderns */}
        <div className="bg-white/80 backdrop-blur-xl border border-slate-200 shadow-sm rounded-full p-1.5 flex gap-1">
          {[
            { id: 'island', label: '🏝️ Floating Island' },
            { id: 'spatial', label: '🥽 VisionOS Spatial' },
            { id: 'dock', label: '📱 iPadOS Dock' },
            { id: 'topnav', label: '☁️ Top Navigation' }
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTheme(t.id as any)}
              className={`px-5 py-2 rounded-full text-[13px] font-bold transition-all duration-300 ${
                theme === t.id ? 'bg-slate-900 text-white shadow-md' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

      </div>

      {/* Preview Container */}
      <div className="w-full max-w-[1200px] mx-auto px-6">
        
        {/* Description Box */}
        <div className="mb-6 bg-white p-5 rounded-[20px] shadow-sm border border-slate-200 flex flex-col items-center text-center">
          {theme === 'integrated' && (
            <>
              <h3 className="text-lg font-bold text-slate-900 mb-1">macOS Integrated Sidebar</h3>
              <p className="text-sm text-slate-600">Sidebar hòa làm một với nền trang chính (cùng sử dụng một dải Gradient xuyên suốt). Lớp kính của Sidebar mỏng hơn Dashboard để tạo sự phân tầng, giống hệt các ứng dụng Mac gốc.</p>
            </>
          )}
          {theme === 'split' && (
            <>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Dual Column (macOS Split View)</h3>
              <p className="text-sm text-slate-600">Thiết kế 2 cột kinh điển của Apple (như Mail, Cài đặt). Một thanh Icon nhỏ siêu tối giản ngoài cùng, và một Sidebar thứ hai chứa các Sub-menu. Cực kỳ chuyên nghiệp cho các hệ thống lớn.</p>
            </>
          )}
          {theme === 'mini' && (
            <>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Minimal Icon Bar</h3>
              <p className="text-sm text-slate-600">Sidebar siêu mỏng chỉ chứa Icon. Phù hợp nếu bạn đã quen thuộc với các chức năng và muốn dành tối đa không gian màn hình cho Dashboard dữ liệu.</p>
            </>
          )}
          {theme === 'island' && (
            <>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Floating Island Sidebar</h3>
              <p className="text-sm text-slate-600">Sidebar tách rời khỏi mép trái màn hình, trở thành một thanh nổi (Island) bồng bềnh độc lập. Giao diện cực kỳ hiện đại, thoáng đãng và đậm chất thiết kế của năm 2026.</p>
            </>
          )}
          {theme === 'spatial' && (
            <>
              <h3 className="text-lg font-bold text-slate-900 mb-1">VisionOS Spatial Concept</h3>
              <p className="text-sm text-slate-600">Mô phỏng giao diện Thực tế ảo của Apple. Sidebar bị biến thành một "viên thuốc" (Pill) bay hoàn toàn độc lập bên ngoài cửa sổ chính. Vẻ đẹp của không gian ba chiều (3D).</p>
            </>
          )}
          {theme === 'dock' && (
            <>
              <h3 className="text-lg font-bold text-slate-900 mb-1">iPadOS Floating Dock</h3>
              <p className="text-sm text-slate-600">Gỡ bỏ hoàn toàn Sidebar bên trái để giải phóng 100% không gian ngang! Điều hướng qua một thanh Dock kính mờ nổi ở cạnh dưới màn hình giống dùng iPad.</p>
            </>
          )}
          {theme === 'topnav' && (
            <>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Top Navigation Bar</h3>
              <p className="text-sm text-slate-600">Kiểu dáng gọn gàng, thanh lịch với thanh Navbar kính mờ ở phía trên cùng. Không gian theo chiều dọc (Vertical) bị giảm một chút, nhưng mở rộng tối đa theo chiều ngang.</p>
            </>
          )}
        </div>

        {/* The Live Interactive Preview */}
        <LayoutPreview theme={theme} />
        
      </div>
    </div>
  );
};

export default NavigationConcepts;
