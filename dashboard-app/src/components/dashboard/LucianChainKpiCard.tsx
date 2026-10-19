// Lucian UX/UI Prompt #050, #098, #049 · MIT License (c) 2026 Seokwoooo · https://lucianlabs.dev/uxui-prompt/
// Adapted for DashBoardD Overview KPI Cards

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowRight, ChevronDown, AlertCircle
} from 'lucide-react';
// ── Lucian #098 Rolling Digits Component ──
export const LucianRollingDigits: React.FC<{ value: number; className?: string }> = ({ value, className = '' }) => {
  const formatted = useMemo(() => Math.max(0, Math.round(value)).toLocaleString('vi-VN'), [value]);
  const chars = formatted.split('');

  return (
    <div className={`lucian-rolling-digits ${className}`} role="img" aria-label={`Số lượng: ${formatted}`}>
      {chars.map((ch, idx) => {
        const isDigit = /\d/.test(ch);
        if (!isDigit) {
          return (
            <span key={idx} className="lucian-sym">
              {ch}
            </span>
          );
        }
        const digitVal = parseInt(ch, 10);
        return (
          <span 
            key={idx} 
            className="lucian-col" 
            style={{ '--d': digitVal, '--i': idx } as React.CSSProperties}
          >
            <span className="lucian-col-inner">
              {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
                <span key={n}>{n}</span>
              ))}
            </span>
          </span>
        );
      })}
    </div>
  );
};

// ── Lucian KPI Card Component ──
export interface LucianChainKpiCardProps {
  title: string;
  chainCode: 'fpt' | 'lc' | 'vac';
  errors: any[];
  colorTheme: 'rose' | 'blue' | 'teal';
  route: string;
  globalMaxCount: number;
  totalSystemErrors?: number;
  activeEmployees?: any[];
}

export const LucianChainKpiCard: React.FC<LucianChainKpiCardProps> = ({
  title,
  chainCode,
  errors,
  colorTheme,
  route,
  globalMaxCount,
  totalSystemErrors = 0,
  activeEmployees = []
}) => {
  const navigate = useNavigate();
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

  const toggleRow = (key: string) => {
    setExpandedRows(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // ── Theme Configurations ──
  const theme = useMemo(() => {
    switch (colorTheme) {
      case 'rose':
        return {
          accentHex: '#E11D48',
          accentSoft: 'rgba(225, 29, 72, 0.1)',
          headerGrad: 'linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 55%, #FECDD3 100%)',
          logoBg: '#DC2626',
          logoText: 'text-rose-600',
          countColor: 'text-slate-900',
          progressFill: 'bg-gradient-to-r from-rose-400 to-rose-500',
          progressTrack: 'bg-rose-100/60',
          badgeText: 'text-rose-600',
          badgeBg: 'bg-rose-50 border border-rose-200/60',
          pillText: 'FPT'
        };
      case 'blue':
        return {
          accentHex: '#2563EB',
          accentSoft: 'rgba(37, 99, 235, 0.1)',
          headerGrad: 'linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 55%, #BFDBFE 100%)',
          logoBg: '#1D4ED8',
          logoText: 'text-blue-700',
          countColor: 'text-slate-900',
          progressFill: 'bg-gradient-to-r from-blue-400 to-blue-600',
          progressTrack: 'bg-blue-100/60',
          badgeText: 'text-blue-600',
          badgeBg: 'bg-blue-50 border border-blue-200/60',
          pillText: 'LC'
        };
      case 'teal':
      default:
        return {
          accentHex: '#0D9488',
          accentSoft: 'rgba(13, 148, 136, 0.1)',
          headerGrad: 'linear-gradient(135deg, #F0FDFA 0%, #CCFBF1 55%, #99F6E4 100%)',
          logoBg: '#0F766E',
          logoText: 'text-teal-700',
          countColor: 'text-slate-900',
          progressFill: 'bg-gradient-to-r from-teal-400 to-teal-600',
          progressTrack: 'bg-teal-100/60',
          badgeText: 'text-teal-600',
          badgeBg: 'bg-teal-50 border border-teal-200/60',
          pillText: 'VAC'
        };
    }
  }, [colorTheme]);

  // Total error count for this chain
  const totalErrors = useMemo(() => {
    return (errors || []).reduce((sum: number, err: any) => sum + (err.count || 0), 0);
  }, [errors]);

  // Sorted errors descending
  const sortedErrors = useMemo(() => {
    return [...(errors || [])].sort((a: any, b: any) => (b.count || 0) - (a.count || 0));
  }, [errors]);

  // System share percentage
  const sharePercentage = useMemo(() => {
    if (totalSystemErrors <= 0) return 0;
    return Math.round((totalErrors / totalSystemErrors) * 100);
  }, [totalErrors, totalSystemErrors]);


  // Employee Name Matcher
  const getEmployeeDisplayName = (rawName: string) => {
    if (!rawName) return 'Không rõ';
    const clean = String(rawName).trim();
    const lower = clean.toLowerCase();
    const matched = activeEmployees.find(emp => {
      const empId = String(emp.id || '').trim().toLowerCase();
      const empName = String(emp.name || '').trim().toLowerCase();
      return (
        empId === lower || 
        empId === lower + '@fpt.com' || 
        lower === empId.replace('@fpt.com', '') ||
        empName === lower
      );
    });
    if (matched?.name) return matched.name;
    return clean.includes('@') ? clean.split('@')[0] : clean;
  };

  return (
    <div 
      className={`lucian-kpi-card lucian-card-${chainCode}`}
      style={{
        '--card-accent': theme.accentHex,
        '--card-accent-soft': theme.accentSoft
      } as React.CSSProperties}
    >
      <div className={`lucian-kpi-inner lucian-inner-${chainCode}`}>
        {/* ── KPI Header Area (#050 + #098 + #049) ── */}
        <div 
          className="lucian-kpi-header"
          style={{ background: theme.headerGrad }}
        >
          {/* Top Row: Chain Name + Spring CTA (#049 / #050) */}
          <div className="flex items-center justify-between relative z-10">
            <span className={`font-black text-[16px] tracking-wide ${theme.logoText}`}>
              {title}
            </span>

            {/* Spring Action CTA Button (#049 / #050) */}
            <button 
              type="button"
              onClick={() => navigate(route)}
              className="lucian-cta-btn"
              title={`Chuyển sang trang chi tiết ${title}`}
            >
              <span>Xem chi tiết</span>
              <ArrowRight size={13} className="lucian-cta-arrow" />
            </button>
          </div>

          {/* Bottom Area: KPI Number (#098 Rolling Digits), Delta Badge & Subtle Chain Watermark */}
          <div className="relative z-10 mt-auto flex items-end justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-[12.5px] font-bold text-slate-600">Tổng lỗi</span>
                {sharePercentage > 0 && (
                  <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-white/85 text-slate-700 shadow-2xs border border-white">
                    {sharePercentage}% toàn hệ thống
                  </span>
                )}
              </div>
              
              <div className="text-[46px] font-black leading-none text-slate-900 tracking-tight">
                <LucianRollingDigits value={totalErrors} />
              </div>
            </div>
          </div>
        </div>

        {/* ── List Header (#050) ── */}
        <div className="lucian-list-header">
          <div className="font-bold text-slate-800 text-[13.5px]">
            <span>Danh sách loại lỗi</span>
          </div>
        </div>

        {/* ── List Body (Ranked Error Rows) ── */}
        <div className="lucian-list-body custom-scrollbar">
          {sortedErrors.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-slate-300 gap-2">
              <AlertCircle size={28} className="opacity-40" />
              <p className="text-[12.5px] italic text-slate-400">Không có dữ liệu lỗi</p>
            </div>
          ) : (
            <div>
              {sortedErrors.map((err: any, idx: number) => {
                const rank = idx + 1;
                const errType = err.type || err.errorType || 'Lỗi không xác định';
                const count = err.count || 0;
                const percentage = globalMaxCount > 0 ? (count / globalMaxCount) * 100 : 0;
                const isExpanded = !!expandedRows[errType];
                const employeeList = (err.employees || err.employeeStats || [])
                  .slice()
                  .sort((a: any, b: any) => (b.count || 0) - (a.count || 0));

                return (
                  <div key={idx} className="border-b border-slate-100/70 last:border-0 transition-colors">
                    <div 
                      onClick={() => toggleRow(errType)}
                      className={`lucian-cat-row ${isExpanded ? 'bg-slate-50/70' : ''}`}
                    >
                      {/* Rank Indicator */}
                      <div className="w-6 shrink-0 flex items-center justify-center mr-2.5">
                        {rank === 1 ? (
                          <span className="lucian-rank-badge lucian-rank-1">1</span>
                        ) : rank === 2 ? (
                          <span className="lucian-rank-badge lucian-rank-2">2</span>
                        ) : rank === 3 ? (
                          <span className="lucian-rank-badge lucian-rank-3">3</span>
                        ) : (
                          <span className="lucian-rank-n text-[12px]">{rank}</span>
                        )}
                      </div>

                      {/* Title & Progress Bar */}
                      <div className="flex-1 min-w-0 mr-3">
                        <div className="text-[12.5px] font-semibold text-slate-800 truncate" title={errType}>
                          {errType}
                        </div>
                        <div className="lucian-progress-track">
                          <div 
                            className={`lucian-progress-fill ${theme.progressFill}`}
                            style={{ width: `${Math.min(100, percentage)}%` }}
                          />
                        </div>
                      </div>

                      {/* Count & Expand Chevron */}
                      <div className="flex items-center gap-2 shrink-0">
                        <span className={`font-black text-[13.5px] ${theme.logoText}`}>
                          {count}
                        </span>
                        <ChevronDown 
                          size={13} 
                          className={`text-slate-400 transition-transform duration-200 ${isExpanded ? 'rotate-180 text-slate-700' : ''}`}
                        />
                      </div>
                    </div>

                    {/* Expandable Employee Breakdown */}
                    {isExpanded && (
                      <div className="px-5 pb-3 pt-1 bg-slate-50/40">
                        <div className={`p-3 rounded-2xl ${theme.badgeBg}`}>
                          {employeeList.length === 0 ? (
                            <div className="text-[11.5px] text-slate-400 italic py-1.5 text-center">
                              Chưa có danh sách nhân viên chi tiết
                            </div>
                          ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto custom-scrollbar pr-1">
                              {employeeList.map((emp: any, j: number) => {
                                const displayName = getEmployeeDisplayName(emp.name || emp.employeeName || emp.employeeId);
                                return (
                                  <div 
                                    key={j} 
                                    className="flex items-center justify-between bg-white px-2.5 py-1.5 rounded-xl border border-slate-100 shadow-2xs"
                                  >
                                    <span className="text-[11.5px] text-slate-700 font-medium truncate pr-2" title={displayName}>
                                      {displayName}
                                    </span>
                                    <span className={`text-[10.5px] font-bold px-1.5 py-0.5 rounded-lg ${theme.badgeText} bg-slate-100/80`}>
                                      {emp.count}
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
