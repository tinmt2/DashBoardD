import React from 'react';

interface CircularSpinnerProps {
  size?: number;
  className?: string;
  strokeWidth?: number;
}

/**
 * Standard SVG circular spinner with smooth rotating animation ("xoay tròn")
 */
export function CircularSpinner({ size = 16, className = "", strokeWidth = 3.2 }: CircularSpinnerProps) {
  return (
    <svg 
      className={`animate-spin ${className}`} 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      style={{ animationDuration: '0.75s' }}
    >
      <circle 
        className="opacity-25" 
        cx="12" 
        cy="12" 
        r="10" 
        stroke="currentColor" 
        strokeWidth={strokeWidth} 
      />
      <path 
        className="opacity-95" 
        fill="currentColor" 
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" 
      />
    </svg>
  );
}

interface RealtimeSyncBannerProps {
  isSyncing: boolean;
  statusText?: string;
  duration: number;
}

/**
 * Floating realtime sync status pill indicating active real-time data synchronization
 */
export function RealtimeSyncBanner({ isSyncing, statusText, duration }: RealtimeSyncBannerProps) {
  if (!isSyncing) return null;

  return (
    <div className="fixed top-5 left-1/2 -translate-x-1/2 z-[9990] pointer-events-none animate-in fade-in slide-in-from-top-3 duration-300">
      <div className="bg-slate-900/95 text-white backdrop-blur-md rounded-full px-4 py-2 border border-slate-700/80 shadow-[0_10px_35px_rgba(0,0,0,0.3)] flex items-center gap-3">
        <div className="relative flex items-center justify-center">
          <CircularSpinner size={16} className="text-emerald-400" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        </div>
        <span className="text-[12.5px] font-semibold text-slate-100 tracking-tight">
          {statusText || 'Đang tải dữ liệu...'}
        </span>
        <div className="flex items-center bg-slate-800/90 text-emerald-400 px-2.5 py-0.5 rounded-full border border-slate-700/60">
          <span className="text-[11.5px] font-bold tabular-nums">{duration}s</span>
        </div>
      </div>
    </div>
  );
}

export default CircularSpinner;
