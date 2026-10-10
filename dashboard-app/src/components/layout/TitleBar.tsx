import React, { useEffect, useState } from 'react';
import { Minus, Square, Copy, X } from 'lucide-react';

declare global {
  interface Window {
    electron?: {
      window: {
        minimize: () => void;
        maximize: () => void;
        close: () => void;
        onStateChange: (callback: (state: boolean) => void) => void;
        removeStateChange: () => void;
      };
    };
  }
}

const TitleBar: React.FC = () => {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    // Only run in Electron environment
    if (window.electron?.window) {
      window.electron.window.onStateChange((state: boolean) => {
        setIsMaximized(state);
      });
      
      return () => {
        window.electron?.window.removeStateChange();
      };
    }
  }, []);

  const handleMinimize = () => {
    if (window.electron?.window) window.electron.window.minimize();
  };

  const handleMaximize = () => {
    if (window.electron?.window) window.electron.window.maximize();
  };

  const handleClose = () => {
    if (window.electron?.window) window.electron.window.close();
  };

  // If not in electron, don't show custom title bar
  if (!window.electron) return null;

  return (
    <div 
      className="flex h-8 items-center justify-between bg-white/40 backdrop-blur-md border-b border-white/60 shrink-0 z-50 select-none relative"
      style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
    >
      <div className="flex items-center gap-3 px-4">
        {/* Empty space for dragging */}
      </div>

      <div 
        className="flex items-center h-full"
        style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
      >
        <button 
          onClick={handleMinimize}
          className="h-full px-4 flex items-center justify-center text-slate-600 hover:bg-black/5 transition-colors"
          title="Minimize"
        >
          <Minus size={16} strokeWidth={2} />
        </button>
        <button 
          onClick={handleMaximize}
          className="h-full px-4 flex items-center justify-center text-slate-600 hover:bg-black/5 transition-colors"
          title={isMaximized ? "Restore" : "Maximize"}
        >
          {isMaximized ? <Copy size={14} strokeWidth={2} /> : <Square size={13} strokeWidth={2} />}
        </button>
        <button 
          onClick={handleClose}
          className="h-full px-4 flex items-center justify-center text-slate-600 hover:bg-red-500 hover:text-white transition-colors"
          title="Close"
        >
          <X size={18} strokeWidth={2} />
        </button>
      </div>
    </div>
  );
};

export default TitleBar;
