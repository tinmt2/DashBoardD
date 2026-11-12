import React from 'react';

export const TitleBar: React.FC = () => {
  // Hide completely when running inside a standard web browser
  if (typeof window === 'undefined' || !window.electronAPI) {
    return null;
  }

  return (
    <div 
      className="h-12 bg-slate-950 flex items-center justify-between select-none px-4 flex-shrink-0"
      style={{ WebkitAppRegion: 'drag' } as any}
    >
      <div className="flex-1" />

      {/* Right: Window Controls */}
      <div className="flex gap-2.5 items-center" style={{ WebkitAppRegion: 'no-drag' } as any}>
        {/* Minimize */}
        <div 
          onClick={() => window.electronAPI?.minimize()}
          className="w-3.5 h-3.5 rounded-full bg-slate-800 border border-slate-700 hover:bg-slate-700 cursor-pointer flex items-center justify-center transition-colors group"
        >
          <svg className="w-2 h-2 text-slate-400 opacity-0 group-hover:opacity-100" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3"><path d="M20 12H4"/></svg>
        </div>
        {/* Maximize */}
        <div 
          onClick={() => window.electronAPI?.maximize()}
          className="w-3.5 h-3.5 rounded-full bg-slate-800 border border-slate-700 hover:bg-slate-700 cursor-pointer flex items-center justify-center transition-colors group"
        >
          <svg className="w-2 h-2 text-slate-400 opacity-0 group-hover:opacity-100" viewBox="0 0 24 24" stroke="currentColor" fill="transparent" strokeWidth="3"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
        </div>
        {/* Close */}
        <div 
          onClick={() => window.electronAPI?.close()}
          className="w-3.5 h-3.5 rounded-full bg-slate-800 border border-slate-700 hover:bg-rose-500 hover:border-rose-500 cursor-pointer flex items-center justify-center transition-all group"
        >
          <svg className="w-2 h-2 text-rose-300 group-hover:text-white opacity-0 group-hover:opacity-100" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </div>
      </div>
    </div>
  );
};
