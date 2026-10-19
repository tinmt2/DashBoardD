/* Lucian UX/UI Prompt #030 Date Range Calendar · MIT License (c) 2026 Seokwoooo · https://lucianlabs.dev/uxui-prompt/ */
import React, { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, Calendar, Check, X } from 'lucide-react';

export interface LucianDateRangePickerProps {
  filterMode: 'all' | number | 'custom';
  startDate: Date | null;
  endDate: Date | null;
  onApply: (mode: 'all' | number | 'custom', start: Date | null, end: Date | null) => void;
  onClose: () => void;
  positionClasses?: string;
}

const WEEKDAYS = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

export const LucianDateRangePicker: React.FC<LucianDateRangePickerProps> = ({
  filterMode,
  startDate,
  endDate,
  onApply,
  onClose,
  positionClasses = 'absolute left-[calc(100%+14px)] top-0'
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize view month based on existing selection or current date
  const today = new Date();
  const initialViewDate = startDate || today;
  const [viewYear, setViewYear] = useState(initialViewDate.getFullYear());
  const [viewMonth, setViewMonth] = useState(initialViewDate.getMonth()); // 0-indexed

  // Draft selection
  const [draftStart, setDraftStart] = useState<Date | null>(startDate);
  const [draftEnd, setDraftEnd] = useState<Date | null>(endDate);
  const [hoverDate, setHoverDate] = useState<Date | null>(null);

  // Close on Escape or click outside
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  // Navigate months
  const handlePrevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear(y => y - 1);
    } else {
      setViewMonth(m => m - 1);
    }
  };

  const handleNextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear(y => y + 1);
    } else {
      setViewMonth(m => m + 1);
    }
  };

  // Format helpers
  const formatDateVN = (d: Date | null) => {
    if (!d) return '--/--/----';
    const day = d.getDate().toString().padStart(2, '0');
    const month = (d.getMonth() + 1).toString().padStart(2, '0');
    return `${day}/${month}/${d.getFullYear()}`;
  };

  const isSameDay = (a: Date | null, b: Date | null) => {
    if (!a || !b) return false;
    return a.getFullYear() === b.getFullYear() &&
           a.getMonth() === b.getMonth() &&
           a.getDate() === b.getDate();
  };

  const isBeforeDay = (a: Date, b: Date) => {
    const da = new Date(a.getFullYear(), a.getMonth(), a.getDate()).getTime();
    const db = new Date(b.getFullYear(), b.getMonth(), b.getDate()).getTime();
    return da < db;
  };

  // Day click logic
  const handleDayClick = (dayDate: Date) => {
    // If future date, ignore
    if (isBeforeDay(today, dayDate)) return;

    if (!draftStart || (draftStart && draftEnd)) {
      // Start a new range
      setDraftStart(dayDate);
      setDraftEnd(null);
    } else if (draftStart && !draftEnd) {
      // If clicking same day, lock single day
      if (isSameDay(dayDate, draftStart)) {
        setDraftEnd(draftStart);
      } else if (isBeforeDay(dayDate, draftStart)) {
        setDraftEnd(draftStart);
        setDraftStart(dayDate);
      } else {
        setDraftEnd(dayDate);
      }
    }
  };

  // Select all days
  const handleSelectAllDays = () => {
    onApply('all', null, null);
    onClose();
  };

  // Final confirmation
  const handleConfirm = () => {
    if (draftStart) {
      const effEnd = draftEnd || draftStart;
      onApply('custom', draftStart, effEnd);
    } else {
      onApply('all', null, null);
    }
    onClose();
  };

  // Build 42 grid cells
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const firstDayIndex = new Date(viewYear, viewMonth, 1).getDay(); // 0 is Sunday
  const daysInPrevMonth = new Date(viewYear, viewMonth, 0).getDate();

  const calendarDays: Array<{
    date: Date;
    isCurrentMonth: boolean;
    isPast: boolean;
    isToday: boolean;
    isFuture: boolean;
  }> = [];

  // Prev month padding
  for (let i = firstDayIndex - 1; i >= 0; i--) {
    const d = new Date(viewYear, viewMonth - 1, daysInPrevMonth - i);
    calendarDays.push({
      date: d,
      isCurrentMonth: false,
      isPast: true,
      isToday: isSameDay(d, today),
      isFuture: isBeforeDay(today, d)
    });
  }

  // Current month days
  for (let d = 1; d <= daysInMonth; d++) {
    const dt = new Date(viewYear, viewMonth, d);
    calendarDays.push({
      date: dt,
      isCurrentMonth: true,
      isPast: isBeforeDay(dt, today),
      isToday: isSameDay(dt, today),
      isFuture: isBeforeDay(today, dt)
    });
  }

  // Next month padding to fill 42 cells
  const remaining = 42 - calendarDays.length;
  for (let d = 1; d <= remaining; d++) {
    const dt = new Date(viewYear, viewMonth + 1, d);
    calendarDays.push({
      date: dt,
      isCurrentMonth: false,
      isPast: false,
      isToday: isSameDay(dt, today),
      isFuture: isBeforeDay(today, dt)
    });
  }

  return (
    <div
      ref={containerRef}
      className={`fixed inset-x-3 top-20 sm:static sm:inset-auto ${positionClasses} z-[100] w-auto sm:w-[340px] max-w-[95vw] mx-auto sm:mx-0 bg-white rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.22),0_0_0_1px_rgba(0,0,0,0.08)] p-4 flex flex-col select-none animate-fade-in text-slate-800`}
    >
      {/* Arrow pointer connecting to sidebar trigger (desktop only) */}
      <div className="hidden sm:block absolute -left-1.5 top-5 w-3.5 h-3.5 bg-white border-l border-t border-slate-200/80 -rotate-45 pointer-events-none rounded-tl-xs shadow-[-3px_-3px_5px_rgba(0,0,0,0.02)]" />

      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Calendar size={15} />
          </div>
          <div>
            <h3 className="text-[13px] font-bold text-slate-800">Chọn khoảng ngày</h3>
            <p className="text-[10.5px] text-slate-400 font-medium">Chọn ngày bắt đầu và kết thúc</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="w-7 h-7 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 flex items-center justify-center transition-colors cursor-pointer"
        >
          <X size={15} />
        </button>
      </div>

      {/* Date Range Selector Header (Lucian #030 style) */}
      <div className="py-3 border-b border-slate-100">
        <div className="grid grid-cols-2 gap-2">
          <div className={`p-2 rounded-xl border text-center transition-all ${
            !draftStart || (draftStart && !draftEnd) ? 'border-indigo-500 bg-indigo-50/50 ring-2 ring-indigo-500/20' : 'border-slate-200 bg-slate-50/50'
          }`}>
            <span className="block text-[9.5px] font-bold uppercase tracking-wider text-slate-400">Từ ngày</span>
            <span className="text-[12px] font-bold text-slate-800">{formatDateVN(draftStart)}</span>
          </div>
          <div className={`p-2 rounded-xl border text-center transition-all ${
            draftStart && draftEnd ? 'border-indigo-500 bg-indigo-50/50 ring-2 ring-indigo-500/20' : 'border-slate-200 bg-slate-50/50'
          }`}>
            <span className="block text-[9.5px] font-bold uppercase tracking-wider text-slate-400">Đến ngày</span>
            <span className="text-[12px] font-bold text-slate-800">{formatDateVN(draftEnd || draftStart)}</span>
          </div>
        </div>
      </div>

      {/* Month Navigation */}
      <div className="flex items-center justify-between pt-3 pb-2 px-1">
        <button
          type="button"
          onClick={handlePrevMonth}
          className="w-7 h-7 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 flex items-center justify-center transition-colors cursor-pointer"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-[13px] font-bold text-slate-800">
          Tháng {viewMonth + 1}, {viewYear}
        </span>
        <button
          type="button"
          onClick={handleNextMonth}
          className="w-7 h-7 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 flex items-center justify-center transition-colors cursor-pointer"
        >
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Weekdays Row */}
      <div className="grid grid-cols-7 text-center pb-1">
        {WEEKDAYS.map((w, idx) => (
          <div key={w} className={`text-[10.5px] font-bold py-1 ${idx === 0 ? 'text-rose-500' : 'text-slate-400'}`}>
            {w}
          </div>
        ))}
      </div>

      {/* Days Grid (42 cells) */}
      <div className="grid grid-cols-7 gap-y-1">
        {calendarDays.map((item, idx) => {
          const { date, isCurrentMonth, isToday, isFuture } = item;
          const isSelectedStart = isSameDay(date, draftStart);
          const isSelectedEnd = isSameDay(date, draftEnd);

          // Range calculation
          let inRange = false;
          if (draftStart && draftEnd) {
            const t = date.getTime();
            const s = new Date(draftStart.getFullYear(), draftStart.getMonth(), draftStart.getDate()).getTime();
            const e = new Date(draftEnd.getFullYear(), draftEnd.getMonth(), draftEnd.getDate()).getTime();
            inRange = t >= Math.min(s, e) && t <= Math.max(s, e);
          } else if (draftStart && hoverDate && !draftEnd) {
            const t = date.getTime();
            const s = new Date(draftStart.getFullYear(), draftStart.getMonth(), draftStart.getDate()).getTime();
            const h = new Date(hoverDate.getFullYear(), hoverDate.getMonth(), hoverDate.getDate()).getTime();
            inRange = t >= Math.min(s, h) && t <= Math.max(s, h);
          }

          const isRangeStart = isSelectedStart || (draftStart && hoverDate && isBeforeDay(hoverDate, draftStart) && isSameDay(date, hoverDate));
          const isRangeEnd = isSelectedEnd || (draftStart && hoverDate && !isBeforeDay(hoverDate, draftStart) && isSameDay(date, hoverDate));
          const isSingle = isSelectedStart && (!draftEnd || isSameDay(draftStart, draftEnd));

          return (
            <div
              key={idx}
              className={`relative flex items-center justify-center py-0.5 ${
                inRange ? 'bg-indigo-50/70 text-indigo-700' : ''
              } ${isRangeStart && inRange && !isSingle ? 'rounded-l-xl' : ''} ${
                isRangeEnd && inRange && !isSingle ? 'rounded-r-xl' : ''
              }`}
            >
              <button
                type="button"
                disabled={isFuture}
                onClick={() => handleDayClick(date)}
                onMouseEnter={() => {
                  if (draftStart && !draftEnd && !isFuture) {
                    setHoverDate(date);
                  }
                }}
                onMouseLeave={() => setHoverDate(null)}
                className={`w-8 h-8 rounded-xl text-[12px] font-semibold flex items-center justify-center transition-all relative cursor-pointer ${
                  !isCurrentMonth ? 'text-slate-300 opacity-40' : 'text-slate-700'
                } ${
                  isFuture ? 'cursor-not-allowed opacity-25 text-slate-300' : 'hover:bg-indigo-100 hover:text-indigo-900'
                } ${
                  isSelectedStart || isSelectedEnd
                    ? 'bg-indigo-600 !text-white !font-bold shadow-sm'
                    : ''
                }`}
              >
                {date.getDate()}
                {isToday && !isSelectedStart && !isSelectedEnd && (
                  <span className="absolute bottom-1 w-1 h-1 rounded-full bg-indigo-600"></span>
                )}
              </button>
            </div>
          );
        })}
      </div>

      {/* Footer Summary & Action Buttons */}
      <div className="pt-3.5 mt-2 border-t border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleSelectAllDays}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer border ${
              filterMode === 'all'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'text-slate-600 hover:text-indigo-600 hover:bg-slate-50 border-slate-200'
            }`}
            title="Xem toàn bộ dữ liệu lịch sử"
          >
            Tất cả ngày
          </button>
          {draftStart && (
            <span className="text-[11px] font-bold text-slate-500">
              {draftEnd ? (
                <>
                  <b className="text-slate-800">{Math.round((new Date(draftEnd.getFullYear(), draftEnd.getMonth(), draftEnd.getDate()).getTime() - new Date(draftStart.getFullYear(), draftStart.getMonth(), draftStart.getDate()).getTime()) / 86400000) + 1}</b> ngày
                </>
              ) : (
                'Chọn ngày kết thúc'
              )}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-xl text-[11.5px] font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            className="px-4 py-1.5 rounded-xl text-[11.5px] font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm hover:shadow transition-all flex items-center gap-1 cursor-pointer"
          >
            <Check size={13} strokeWidth={2.5} />
            <span>Áp dụng</span>
          </button>
        </div>
      </div>
    </div>
  );
};
