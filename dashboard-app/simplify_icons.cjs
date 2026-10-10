const fs = require('fs');
let code = fs.readFileSync('src/pages/Dashboard.tsx', 'utf8');

// The block to replace:
// from `<div className="flex items-center gap-2 mr-2">`
// to `<ChevronDown size={14} strokeWidth={2.5} />\n              </button>`

const searchRegex = /<div className="flex items-center gap-2 mr-2">[\s\S]*?<ChevronDown size=\{14\} strokeWidth=\{2\.5\} \/>\s*<\/button>/;

const replacement = `<div className="flex items-center gap-1 mr-2">
                {authState?.authenticated ? (
                   <span className="flex items-center justify-center w-9 h-9 rounded-full text-emerald-500" title="Connected">
                     <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                   </span>
                ) : authState?.status === 'STARTING' || authState?.status === 'LOGIN_REQUIRED' || authState?.status === 'LOGIN_PAGE' || authState?.status === 'NAVIGATING' ? (
                   <button onClick={handleStartAuth} className="flex items-center justify-center w-9 h-9 rounded-full text-amber-500 hover:bg-amber-50 transition-colors cursor-pointer" title="Đang chờ đăng nhập...">
                     <RefreshCw size={18} strokeWidth={2} className="animate-spin" />
                   </button>
                ) : authState?.status === 'OTP_REQUIRED' ? (
                   <button onClick={handleStartAuth} className="flex items-center gap-1.5 text-[13px] font-bold text-indigo-600 bg-indigo-50 px-3 py-1.5 rounded-full hover:bg-indigo-100 transition-colors cursor-pointer" title="Nhập OTP">
                       <AlertCircle size={14} strokeWidth={2} /> Nhập OTP
                   </button>
                ) : authState?.status === 'ERROR' ? (
                   <button onClick={handleStartAuth} className="flex items-center justify-center w-9 h-9 rounded-full text-rose-500 hover:bg-rose-50 transition-colors" title="Lỗi đăng nhập">
                     <AlertCircle size={18} strokeWidth={2} />
                   </button>
                ) : (
                   <button onClick={handleStartAuth} className="flex items-center gap-1.5 px-3 h-9 rounded-full text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors" title="Đăng nhập">
                       <Users size={16} strokeWidth={2} />
                       <span className="text-[13px] font-semibold">Đăng nhập</span>
                   </button>
                )}
              </div>
              <button onClick={() => fileInputRef.current?.click()} className="w-9 h-9 flex items-center justify-center text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors" title="Import Excel">
                <UploadCloud size={18} strokeWidth={2} />
              </button>
              <button onClick={handleSync} disabled={isSyncing} className="w-9 h-9 flex items-center justify-center text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-colors disabled:opacity-50" title="Đồng bộ (Sync)">
                 <RefreshCw size={18} strokeWidth={2} className={isSyncing ? "animate-spin text-indigo-600" : ""} />
              </button>
              <button className="px-3 h-9 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-full text-[13px] font-semibold flex items-center gap-1.5 transition-colors ml-1">
                7 ngày qua
                <ChevronDown size={14} strokeWidth={2.5} />
              </button>`;

if (searchRegex.test(code)) {
    code = code.replace(searchRegex, replacement);
    fs.writeFileSync('src/pages/Dashboard.tsx', code, 'utf8');
    console.log("Successfully replaced buttons block");
} else {
    console.log("Could not find the block to replace");
}
