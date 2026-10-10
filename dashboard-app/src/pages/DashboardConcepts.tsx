import React, { useState } from 'react';
import { ShieldAlert, TrendingDown, ChevronDown } from 'lucide-react';

// MOCK DATA
const kpiData = {
  total: 872,
  checked: 4560,
  rate: '19.1%',
  employees: 142
};

const chainData = [
  { name: 'FPT Shop', errors: 420, rate: 20.0, color: '#FF3B30' },
  { name: 'Long Châu', errors: 285, rate: 18.8, color: '#007AFF' },
  { name: 'Vaccine', errors: 167, rate: 17.8, color: '#34C759' },
];

const errorTypes = [
  { name: 'Thiếu thông tin', value: 350 },
  { name: 'Sai phân loại', value: 250 },
  { name: 'Sai quy trình', value: 150 },
  { name: 'Thái độ nhân viên', value: 122 },
];

const topEmployees = [
  { name: 'Nguyễn Văn A', chain: 'FPT Shop', errors: 45, avatar: 'https://i.pravatar.cc/150?u=a' },
  { name: 'Trần Thị B', chain: 'Long Châu', errors: 38, avatar: 'https://i.pravatar.cc/150?u=b' },
  { name: 'Lê Văn C', chain: 'Vaccine', errors: 32, avatar: 'https://i.pravatar.cc/150?u=c' },
];

type ThemeType = 'sonoma' | 'visionos' | 'ios' | 'vercel' | 'stripe' | 'material' | 'neobrutal';

// REUSABLE CARD COMPONENT
const ThemeCard = ({ children, theme, className = '' }: { children: React.ReactNode, theme: ThemeType, className?: string }) => {
  let style: React.CSSProperties = {};
  
  switch (theme) {
    case 'sonoma':
      style = { backgroundColor: 'rgba(255, 255, 255, 0.4)', backdropFilter: 'blur(40px) saturate(150%)', WebkitBackdropFilter: 'blur(40px) saturate(150%)', borderRadius: '24px', border: '1px solid rgba(255, 255, 255, 0.6)', boxShadow: '0 8px 32px rgba(0,0,0,0.06)' };
      break;
    case 'visionos':
      style = { backgroundColor: 'rgba(255, 255, 255, 0.25)', backdropFilter: 'blur(30px)', WebkitBackdropFilter: 'blur(30px)', borderRadius: '28px', border: '1px solid rgba(255, 255, 255, 0.4)', boxShadow: '0 8px 32px rgba(0,0,0,0.08), inset 0 2px 2px rgba(255,255,255,0.8), inset 0 -1px 2px rgba(255,255,255,0.3)' };
      break;
    case 'ios':
      style = { backgroundColor: 'rgba(255, 255, 255, 0.7)', backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)', borderRadius: '20px', border: '1px solid rgba(255, 255, 255, 0.9)', boxShadow: '0 4px 16px rgba(0,0,0,0.03)' };
      break;
    case 'vercel':
      style = { backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #eaeaea', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' };
      break;
    case 'stripe':
      style = { backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #f1f5f9', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)' };
      break;
    case 'material':
      style = { backgroundColor: '#f0f4f8', borderRadius: '28px', border: 'none', boxShadow: 'none' };
      break;
    case 'neobrutal':
      style = { backgroundColor: '#ffffff', borderRadius: '12px', border: '3px solid #0f172a', boxShadow: '6px 6px 0px #0f172a' };
      break;
  }

  return (
    <div className={className} style={style}>
      {children}
    </div>
  );
};

const DashboardTemplate = ({ theme }: { theme: ThemeType }) => {
  // Define text colors based on theme
  let textColor = '#1d1d1f';
  let subColor = '#86868b';
  let accentColor = '#FF3B30';
  let fontClass = 'font-sans';

  if (['vercel'].includes(theme)) {
    textColor = '#000000';
    subColor = '#666666';
    fontClass = 'font-sans tracking-tight';
  } else if (['stripe'].includes(theme)) {
    textColor = '#0f172a';
    subColor = '#64748b';
    accentColor = '#ef4444';
  } else if (theme === 'material') {
    textColor = '#1e293b';
    subColor = '#475569';
  } else if (theme === 'neobrutal') {
    textColor = '#0f172a';
    subColor = '#334155';
    fontClass = 'font-mono tracking-tight'; // gives it a slightly more brutalist feel
  }
  
  return (
    <div className={`w-full max-w-[1400px] mx-auto p-8 space-y-6 animate-fade-in relative z-10 ${fontClass}`}>
      
      {/* Header */}
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-[32px] font-bold" style={{ color: textColor }}>Tổng quan lỗi</h1>
          <p className="text-[15px] font-medium mt-1" style={{ color: subColor }}>Cập nhật lần cuối: 14:30 Hôm nay</p>
        </div>
        <div className="flex gap-3">
          <ThemeCard theme={theme} className="px-4 py-2 flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity">
            <span className="text-[14px] font-semibold" style={{ color: textColor }}>7 ngày qua</span>
            <ChevronDown size={16} color={textColor} />
          </ThemeCard>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-6">
        <ThemeCard theme={theme} className="p-6 flex flex-col justify-between h-[160px]">
          <div className="text-[13px] font-bold uppercase tracking-wider" style={{ color: subColor }}>Tổng lỗi</div>
          <div>
            <div className="text-[44px] font-bold leading-none mb-2" style={{ color: textColor }}>{kpiData.total}</div>
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-medium" style={{ color: subColor }}>Ticket</span>
              <span className="text-[12px] font-bold px-2 py-0.5 rounded-md" style={{ color: accentColor, backgroundColor: `${accentColor}1A` }}>12.4%</span>
            </div>
          </div>
        </ThemeCard>
        
        <ThemeCard theme={theme} className="p-6 flex flex-col justify-between h-[160px]">
          <div className="text-[13px] font-bold uppercase tracking-wider" style={{ color: subColor }}>Đã kiểm tra</div>
          <div>
            <div className="text-[44px] font-bold leading-none mb-2" style={{ color: textColor }}>{kpiData.checked.toLocaleString('vi-VN')}</div>
            <div className="text-[13px] font-medium" style={{ color: subColor }}>Ticket</div>
          </div>
        </ThemeCard>

        <ThemeCard theme={theme} className="p-6 flex flex-col justify-between h-[160px]">
          <div className="text-[13px] font-bold uppercase tracking-wider" style={{ color: subColor }}>Tỷ lệ lỗi</div>
          <div>
            <div className="text-[44px] font-bold leading-none mb-2" style={{ color: textColor }}>{kpiData.rate}</div>
            <div className="text-[13px] font-medium" style={{ color: subColor }}>Mục tiêu &lt; 15%</div>
          </div>
        </ThemeCard>

        <ThemeCard theme={theme} className="p-6 flex flex-col justify-between h-[160px]">
          <div className="text-[13px] font-bold uppercase tracking-wider" style={{ color: subColor }}>Nhân viên có lỗi</div>
          <div>
            <div className="text-[44px] font-bold leading-none mb-2" style={{ color: textColor }}>{kpiData.employees}</div>
            <div className="text-[13px] font-medium" style={{ color: subColor }}>/ 450 nhân viên</div>
          </div>
        </ThemeCard>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-3 gap-6 h-auto min-h-[400px]">
        
        {/* Error by Chain */}
        <ThemeCard theme={theme} className="col-span-1 p-6 flex flex-col">
          <h3 className="text-[16px] font-bold mb-6" style={{ color: textColor }}>Lỗi theo chuỗi</h3>
          <div className="flex-1 space-y-6">
            {chainData.map((c, i) => (
              <div key={i}>
                <div className="flex justify-between items-end mb-2">
                  <span className="text-[14px] font-bold" style={{ color: textColor }}>{c.name}</span>
                  <div className="flex gap-3 items-baseline">
                    <span className="text-[14px] font-bold" style={{ color: textColor }}>{c.errors}</span>
                    <span className="text-[12px] font-medium" style={{ color: subColor }}>{c.rate}%</span>
                  </div>
                </div>
                <div className="h-2 w-full bg-black/5 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${(c.errors/chainData[0].errors)*100}%`, backgroundColor: c.color }} />
                </div>
              </div>
            ))}
          </div>
        </ThemeCard>

        {/* Top Error Types */}
        <ThemeCard theme={theme} className="col-span-1 p-6 flex flex-col">
          <h3 className="text-[16px] font-bold mb-6" style={{ color: textColor }}>Loại lỗi phổ biến</h3>
          <div className="flex-1 space-y-5">
            {errorTypes.map((err, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-[13px] font-bold w-5 opacity-40" style={{ color: textColor }}>0{i+1}</span>
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-[14px] font-bold" style={{ color: textColor }}>{err.name}</span>
                    <span className="text-[14px] font-bold" style={{ color: textColor }}>{err.value}</span>
                  </div>
                  <div className="h-1.5 w-full bg-black/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-blue-500/80" style={{ width: `${(err.value/errorTypes[0].value)*100}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ThemeCard>

        {/* Top Employees */}
        <ThemeCard theme={theme} className="col-span-1 p-6 flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-[16px] font-bold" style={{ color: textColor }}>Nhân viên có lỗi</h3>
            <button className="text-[13px] font-bold text-blue-600 hover:underline">Xem tất cả</button>
          </div>
          <div className="flex-1 space-y-4">
            {topEmployees.map((emp, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-[12px] hover:bg-black/5 transition-colors cursor-pointer">
                <div className="flex items-center gap-3">
                  <img src={emp.avatar} alt="" className="w-10 h-10 rounded-full border border-black/10" />
                  <div>
                    <div className="text-[14px] font-bold" style={{ color: textColor }}>{emp.name}</div>
                    <div className="text-[12px] font-medium" style={{ color: subColor }}>{emp.chain}</div>
                  </div>
                </div>
                <div className="text-[14px] font-bold" style={{ color: accentColor }}>{emp.errors} lỗi</div>
              </div>
            ))}
          </div>
        </ThemeCard>

      </div>
    </div>
  );
};

const DashboardConcepts: React.FC = () => {
  const [theme, setTheme] = useState<ThemeType>('sonoma');
  const [bgTheme, setBgTheme] = useState<'colorful' | 'aurora' | 'slate' | 'sand' | 'solid'>('aurora');

  // Background style varies based on selected theme
  const getBackground = () => {
    // If a non-glass template is selected, we tone down the background significantly to make the solid cards pop properly.
    if (['vercel', 'stripe', 'neobrutal'].includes(theme)) {
       return 'none';
    }

    if (bgTheme === 'colorful') {
      return 'radial-gradient(circle at 15% 50%, rgba(179, 212, 255, 0.7), transparent 45%), radial-gradient(circle at 85% 30%, rgba(255, 204, 229, 0.6), transparent 45%), radial-gradient(circle at 50% 80%, rgba(193, 240, 219, 0.7), transparent 45%)';
    }
    if (bgTheme === 'aurora') {
      return 'radial-gradient(circle at 0% 0%, rgba(14, 165, 233, 0.25), transparent 50%), radial-gradient(circle at 100% 100%, rgba(99, 102, 241, 0.2), transparent 50%), radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.15), transparent 60%)';
    }
    if (bgTheme === 'slate') {
      return 'radial-gradient(circle at 20% 0%, rgba(203, 213, 225, 0.6), transparent 50%), radial-gradient(circle at 80% 100%, rgba(148, 163, 184, 0.4), transparent 50%)';
    }
    if (bgTheme === 'sand') {
      return 'radial-gradient(circle at 10% 20%, rgba(245, 230, 211, 0.8), transparent 60%), radial-gradient(circle at 90% 80%, rgba(230, 215, 200, 0.7), transparent 60%)';
    }
    return 'none'; // solid
  };

  const getBaseColor = () => {
    // Override base color for specific non-glass themes to ensure perfect contrast
    if (theme === 'vercel') return '#fafafa';
    if (theme === 'stripe') return '#f8fafc';
    if (theme === 'material') return '#fdfcfb';
    if (theme === 'neobrutal') return '#e2e8f0';

    if (bgTheme === 'colorful') return '#f5f5f7';
    if (bgTheme === 'aurora') return '#f0f9ff';
    if (bgTheme === 'slate') return '#f1f5f9';
    if (bgTheme === 'sand') return '#fdfbf7';
    return '#e2e8f0'; // solid slate
  };

  return (
    <div className="relative min-h-screen overflow-x-hidden font-sans pb-12">
      
      {/* Dynamic Background */}
      <div 
        className="fixed inset-0 z-0 transition-all duration-1000"
        style={{
          backgroundColor: getBaseColor(),
          backgroundImage: getBackground(),
          filter: 'blur(30px)',
          transform: 'scale(1.1)'
        }}
      />

      {/* Theme Selectors Topbar */}
      <div className="relative z-20 flex flex-col items-center pt-8 mb-4 gap-6">
        
        {/* Style Category 1: Apple Glass */}
        <div className="flex flex-col items-center gap-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Hiệu ứng Kính (Apple)</span>
          <div className="bg-white/60 backdrop-blur-xl border border-white/80 shadow-[0_8px_32px_rgba(0,0,0,0.06)] rounded-full p-1.5 flex gap-2">
            {[
              { id: 'sonoma', label: 'macOS Sonoma' },
              { id: 'visionos', label: 'VisionOS Spatial' },
              { id: 'ios', label: 'iOS Minimal' }
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setTheme(t.id as any)}
                className={`px-5 py-2 rounded-full text-[14px] font-bold transition-all duration-300 ${
                  theme === t.id 
                    ? 'bg-white text-black shadow-sm' 
                    : 'text-slate-600 hover:text-black hover:bg-white/40'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Style Category 2: Modern SaaS */}
        <div className="flex flex-col items-center gap-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Phong cách Mới (SaaS/Minimalist)</span>
          <div className="bg-white/60 backdrop-blur-xl border border-white/80 shadow-[0_8px_32px_rgba(0,0,0,0.06)] rounded-full p-1.5 flex gap-2 flex-wrap justify-center max-w-2xl">
            {[
              { id: 'vercel', label: 'Vercel / Linear (Siêu mỏng)' },
              { id: 'stripe', label: 'Stripe (Doanh nghiệp)' },
              { id: 'material', label: 'Material 3 (Bo góc lớn)' },
              { id: 'neobrutal', label: 'Neo-Brutalism (Độc lạ)' }
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setTheme(t.id as any)}
                className={`px-5 py-2 rounded-full text-[13px] font-bold transition-all duration-300 ${
                  theme === t.id 
                    ? 'bg-slate-800 text-white shadow-sm' 
                    : 'text-slate-600 hover:text-black hover:bg-white/60'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Background Color Selector (Only show for Glass themes) */}
        {['sonoma', 'visionos', 'ios'].includes(theme) && (
          <div className="mt-2 flex flex-col items-center gap-2 animate-fade-in">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Đổi nền kính</span>
            <div className="bg-white/40 backdrop-blur-md border border-white/40 shadow-sm rounded-full p-1 flex gap-1">
              {[
                { id: 'aurora', label: '🌊 Aurora Blue' },
                { id: 'slate', label: '🏢 Silver Slate' },
                { id: 'sand', label: '☕ Warm Sand' },
                { id: 'colorful', label: '🎨 Mac Pastel' },
                { id: 'solid', label: '⬜ Solid Gray' }
              ].map(t => (
                <button
                  key={t.id}
                  onClick={() => setBgTheme(t.id as any)}
                  className={`px-4 py-1.5 rounded-full text-[12px] font-bold transition-all duration-300 ${
                    bgTheme === t.id 
                      ? 'bg-white/80 text-black shadow-sm border border-white' 
                      : 'text-slate-600 hover:text-black hover:bg-white/30 border border-transparent'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        )}

      </div>

      <div className="mt-4">
        <DashboardTemplate theme={theme} />
      </div>
    </div>
  );
};

export default DashboardConcepts;
