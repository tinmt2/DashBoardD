import React, { useState } from 'react';
import { ArrowUpRight, ArrowDownRight, Activity, Users, Map, AlertCircle } from 'lucide-react';
import { GlassCard } from '../components/common/GlassCard';

type KPITheme = 'bento' | 'pill' | 'hero' | 'natural';

const KPIConcepts: React.FC = () => {
  const [theme, setTheme] = useState<KPITheme>('bento');

  // Mock data for the KPIs
  const kpiData = {
    total: 872,
    checked: 4560,
    rate: '19.1%',
    employees: 142,
    target: '< 15%',
    change: -12.4
  };

  return (
    <div className="min-h-full font-sans pb-12 relative animate-fade-in">
      
      {/* Background to make the Glass pop */}
      <div 
        className="fixed inset-0 z-0"
        style={{
          backgroundColor: '#f0f9ff',
          backgroundImage: 'radial-gradient(circle at 0% 0%, rgba(14, 165, 233, 0.25), transparent 50%), radial-gradient(circle at 100% 100%, rgba(99, 102, 241, 0.2), transparent 50%), radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.15), transparent 60%)',
          filter: 'blur(30px)',
          transform: 'scale(1.1)'
        }}
      />

      <div className="relative z-10 w-full max-w-5xl mx-auto pt-10 px-8">
        
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-[32px] font-bold text-slate-800 tracking-tight mb-3">Chế độ hiển thị KPI</h1>
          <p className="text-[15px] text-slate-600 max-w-2xl mx-auto">
            Thay vì hiển thị 4 khối vuông nhàm chán bằng nhau, dưới đây là các cách sắp xếp thông tin sáng tạo và hiện đại hơn để tập trung sự chú ý của người dùng vào số liệu quan trọng nhất.
          </p>
        </div>

        {/* Selectors */}
        <div className="flex justify-center mb-12">
          <div className="bg-white/70 backdrop-blur-xl border border-white shadow-sm rounded-full p-1.5 flex gap-1">
            {[
              { id: 'bento', label: '🍱 Bento Grid (Khuyên dùng)' },
              { id: 'pill', label: '💊 Unified Pill (Thanh ngang)' },
              { id: 'hero', label: '🦸‍♂️ Hero Typography (Cực lớn)' },
              { id: 'natural', label: '💬 Natural Language (Kể chuyện)' }
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setTheme(t.id as any)}
                className={`px-6 py-2.5 rounded-full text-[13px] font-bold transition-all duration-300 ${
                  theme === t.id 
                    ? 'bg-blue-600 text-white shadow-md' 
                    : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* ============================================================== */}
        {/* PREVIEW CONTAINER */}
        {/* ============================================================== */}
        <div className="w-full">

          {/* 1. BENTO GRID */}
          {theme === 'bento' && (
            <div className="animate-fade-in">
              <div className="mb-4 ml-2">
                <h3 className="text-lg font-bold text-slate-800">Bento Grid Layout</h3>
                <p className="text-sm text-slate-600">Nhấn mạnh vào con số Tổng Lỗi (Lớn nhất ở bên trái), các số liệu phụ được xếp thành cụm ở bên phải.</p>
              </div>
              
              <div className="grid grid-cols-12 gap-5 h-[220px]">
                {/* Hero Block (8 cols) */}
                <GlassCard className="col-span-7 p-8 flex flex-col justify-between relative overflow-hidden">
                  <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600">
                        <AlertCircle size={16} strokeWidth={2.5} />
                      </div>
                      <span className="text-[14px] font-bold text-slate-500 uppercase tracking-widest">Tổng lỗi hệ thống</span>
                    </div>
                    <div className="text-[72px] font-black text-slate-800 leading-none tracking-tighter mt-4">{kpiData.total}</div>
                    
                    <div className="flex items-center gap-3 mt-6">
                      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-red-100 text-red-600 text-[13px] font-bold">
                        <ArrowDownRight size={16} strokeWidth={3} /> {Math.abs(kpiData.change)}% so với tuần trước
                      </div>
                    </div>
                  </div>
                  {/* Decorative faint icon */}
                  <AlertCircle className="absolute -bottom-10 -right-10 text-red-600/5" size={240} />
                </GlassCard>

                {/* Side Blocks (5 cols) */}
                <div className="col-span-5 grid grid-rows-3 gap-5">
                  <GlassCard className="row-span-1 px-6 py-0 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Activity size={18} className="text-slate-400" />
                      <span className="text-[13px] font-bold text-slate-500 uppercase">Đã kiểm tra</span>
                    </div>
                    <span className="text-[20px] font-bold text-slate-800">{kpiData.checked.toLocaleString('vi-VN')}</span>
                  </GlassCard>

                  <GlassCard className="row-span-1 px-6 py-0 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Activity size={18} className="text-blue-500" />
                      <span className="text-[13px] font-bold text-slate-500 uppercase">Tỷ lệ lỗi</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-[20px] font-bold text-slate-800">{kpiData.rate}</span>
                      <span className="text-[11px] font-semibold text-slate-400">Mục tiêu {kpiData.target}</span>
                    </div>
                  </GlassCard>

                  <GlassCard className="row-span-1 px-6 py-0 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Users size={18} className="text-orange-500" />
                      <span className="text-[13px] font-bold text-slate-500 uppercase">Nhân sự vi phạm</span>
                    </div>
                    <span className="text-[20px] font-bold text-slate-800">{kpiData.employees}</span>
                  </GlassCard>
                </div>
              </div>
            </div>
          )}

          {/* 2. UNIFIED PILL */}
          {theme === 'pill' && (
            <div className="animate-fade-in">
              <div className="mb-4 ml-2">
                <h3 className="text-lg font-bold text-slate-800">Unified Pill (Thanh ngang liên tục)</h3>
                <p className="text-sm text-slate-600">Gộp tất cả vào một dải băng duy nhất, siêu tiết kiệm chiều dọc, giống thanh trạng thái server.</p>
              </div>

              <GlassCard className="flex items-center px-2 py-2 rounded-full divide-x divide-black/10">
                <div className="flex-1 px-8 py-4 flex items-center justify-between">
                  <div>
                    <div className="text-[12px] font-bold text-slate-500 uppercase tracking-widest mb-1">Tổng lỗi</div>
                    <div className="text-[32px] font-bold text-slate-800 leading-none">{kpiData.total}</div>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600"><AlertCircle size={20} /></div>
                </div>

                <div className="flex-1 px-8 py-4 flex items-center justify-between">
                  <div>
                    <div className="text-[12px] font-bold text-slate-500 uppercase tracking-widest mb-1">Đã kiểm tra</div>
                    <div className="text-[32px] font-bold text-slate-800 leading-none">{kpiData.checked.toLocaleString('vi-VN')}</div>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500"><Activity size={20} /></div>
                </div>

                <div className="flex-1 px-8 py-4 flex items-center justify-between">
                  <div>
                    <div className="text-[12px] font-bold text-slate-500 uppercase tracking-widest mb-1">Tỷ lệ lỗi</div>
                    <div className="text-[32px] font-bold text-slate-800 leading-none">{kpiData.rate}</div>
                  </div>
                  <div className="text-[12px] font-bold text-blue-600 bg-blue-100 px-2 py-1 rounded-md">{kpiData.target}</div>
                </div>

                <div className="flex-1 px-8 py-4 flex items-center justify-between">
                  <div>
                    <div className="text-[12px] font-bold text-slate-500 uppercase tracking-widest mb-1">Nhân sự có lỗi</div>
                    <div className="text-[32px] font-bold text-slate-800 leading-none">{kpiData.employees}</div>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center text-orange-500"><Users size={20} /></div>
                </div>
              </GlassCard>
            </div>
          )}

          {/* 3. HERO TYPOGRAPHY */}
          {theme === 'hero' && (
            <div className="animate-fade-in">
              <div className="mb-4 ml-2">
                <h3 className="text-lg font-bold text-slate-800">Hero Typography</h3>
                <p className="text-sm text-slate-600">Loại bỏ hoàn toàn các thẻ viền. Dùng chữ cái cỡ siêu lớn (Typography) thả trôi giữa màn hình để tạo cảm giác Magazine/Poster.</p>
              </div>

              <div className="flex items-end justify-between px-8 py-12">
                <div className="flex flex-col">
                  <span className="text-[16px] font-bold text-slate-500 uppercase tracking-widest mb-4">Tổng lỗi toàn hệ thống</span>
                  <div className="flex items-start gap-4">
                    <span className="text-[140px] font-black text-slate-900 leading-[0.8] tracking-tighter">{kpiData.total}</span>
                    <div className="flex flex-col gap-2 mt-4">
                      <span className="px-3 py-1 bg-red-100 text-red-600 rounded-full text-[14px] font-bold inline-block border border-red-200">↑ {Math.abs(kpiData.change)}%</span>
                      <span className="text-[14px] font-semibold text-slate-500">so với 7 ngày trước</span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-16 pb-4">
                  <div>
                    <div className="text-[14px] font-bold text-slate-500 uppercase tracking-widest mb-2">Đã kiểm tra</div>
                    <div className="text-[36px] font-bold text-slate-800">{kpiData.checked.toLocaleString('vi-VN')}</div>
                  </div>
                  <div>
                    <div className="text-[14px] font-bold text-slate-500 uppercase tracking-widest mb-2">Tỷ lệ lỗi</div>
                    <div className="text-[36px] font-bold text-slate-800">{kpiData.rate}</div>
                  </div>
                  <div>
                    <div className="text-[14px] font-bold text-slate-500 uppercase tracking-widest mb-2">Nhân sự vi phạm</div>
                    <div className="text-[36px] font-bold text-slate-800">{kpiData.employees}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 4. NATURAL LANGUAGE */}
          {theme === 'natural' && (
            <div className="animate-fade-in">
              <div className="mb-4 ml-2">
                <h3 className="text-lg font-bold text-slate-800">Natural Language (Văn bản tự nhiên)</h3>
                <p className="text-sm text-slate-600">Thay vì đọc bảng số khô khan, báo cáo được đọc ra như một câu chuyện. Rất thân thiện với người dùng không giỏi số liệu.</p>
              </div>

              <GlassCard className="p-10 max-w-4xl">
                <p className="text-[32px] font-medium text-slate-600 leading-relaxed tracking-tight">
                  Trong 7 ngày qua, hệ thống đã ghi nhận <span className="font-bold text-red-600 bg-red-100/50 px-3 py-1 rounded-xl mx-1 inline-block border border-red-200/50">{kpiData.total} lỗi</span> 
                  trên tổng số <span className="font-bold text-slate-900 border-b-2 border-slate-300 pb-1 mx-1">{kpiData.checked.toLocaleString('vi-VN')} ticket</span> được kiểm tra. 
                  Tỷ lệ lỗi hiện tại ở mức <span className="font-bold text-blue-600 bg-blue-100/50 px-3 py-1 rounded-xl mx-1 inline-block border border-blue-200/50">{kpiData.rate}</span> 
                  (vượt qua mục tiêu {kpiData.target}). 
                  Có <span className="font-bold text-orange-600 bg-orange-100/50 px-3 py-1 rounded-xl mx-1 inline-block border border-orange-200/50">{kpiData.employees} nhân viên</span> liên quan đến các lỗi này.
                </p>
              </GlassCard>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default KPIConcepts;
