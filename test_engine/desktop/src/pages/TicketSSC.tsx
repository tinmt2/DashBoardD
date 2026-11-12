import React, { useState, useEffect } from 'react';
import { useTaskContext } from '../context/TaskContext';
import { ticketApi } from '../api/ticket';
import type { TicketJobState } from '../api/ticket';

const TICKET_TYPES = [
  'Camera MKN', 
  'Lỗi Đầu ghi', 
  'Cam không có playback', 
  'Lỗi ổ cứng'
];

const TicketSSC: React.FC = () => {
  const { tasks, startTask } = useTaskContext();
  const task = tasks['ticket'];
    const jobState = task as any as TicketJobState;
  
  const [activeJobType, setActiveJobType] = useState<string | null>(null);
  const [ticketData, setTicketData] = useState<Record<string, { total: number, created: number, loading: boolean, error?: string, data: any[] }>>({});
  const [globalLoading, setGlobalLoading] = useState(true);
  
  const [modalState, setModalState] = useState<{
    isOpen: boolean;
    type: 'confirm' | 'success' | 'error';
    title: string;
    message: string;
  }>({ isOpen: false, type: 'confirm', title: '', message: '' });

  const countCreated = (data: any[]) => {
    return data.filter(r => {
      const keys = Object.keys(r);
      const ticketKey = keys.find(k => ['ticket', 'ticket id', 'ticket_id'].includes(k.toLowerCase()));
      return ticketKey && r[ticketKey] && r[ticketKey] !== '-' && r[ticketKey] !== '';
    }).length;
  };

  const fetchAllGSheet = async (retryCount = 0) => {
    setGlobalLoading(true);
    const newState: any = {};
    for (const type of TICKET_TYPES) {
      newState[type] = { total: 0, created: 0, loading: true, data: [] };
    }
    setTicketData(newState);
    let hasConnectionError = false;

    for (const type of TICKET_TYPES) {
      try {
        const json = await ticketApi.getTicketData(type);

        if (json.success && Array.isArray(json.data)) {
           const ticketList = json.data;
           const created = countCreated(ticketList);
           setTicketData(prev => ({ ...prev, [type]: { total: ticketList.length, created, loading: false, data: ticketList } }));
        } else {
           setTicketData(prev => ({ ...prev, [type]: { total: 0, created: 0, loading: false, error: json.message, data: [] } }));
        }
      } catch (err: any) {
        const errMsg = err?.message || String(err);
        if (errMsg.includes('Failed to fetch') || errMsg.includes('ERR_CONNECTION_REFUSED') || errMsg.includes('NetworkError')) {
          hasConnectionError = true;
        }
        setTicketData(prev => ({ ...prev, [type]: { total: 0, created: 0, loading: false, error: errMsg, data: [] } }));
      }
    }
    if (hasConnectionError && retryCount < 4) {
      setTimeout(() => {
        fetchAllGSheet(retryCount + 1);
      }, 2000);
      return;
    }
    setGlobalLoading(false);
  };

  useEffect(() => {
    fetchAllGSheet();
  }, []);

  // Automatically refresh data when a job completes
  useEffect(() => {
    if (jobState?.status === 'completed') {
      fetchAllGSheet();
    }
  }, [jobState?.status]);

  const isRunning = jobState?.status === 'running' || jobState?.status === 'queued';

  const startJob = async (type: string) => {
    if (isRunning) return;
    setActiveJobType(type);
    const res = await ticketApi.createJob(null, type);
    if (res.success && res.data) {
      startTask('ticket', res.data.job_id);
    } else {
      setActiveJobType(null);
      setModalState({ isOpen: true, type: 'error', title: 'Không thể tạo tiến trình', message: res.message || 'Lỗi hệ thống.' });
    }
  };

  const startCheckJob = async (type: string) => {
    if (isRunning) return;
    setActiveJobType(type);
    const res = await ticketApi.checkJob(null, type);
    if (res.success && res.data) {
      startTask('ticket', res.data.job_id);
    } else {
      setActiveJobType(null);
      setModalState({ isOpen: true, type: 'error', title: 'Không thể kiểm tra tiến trình', message: res.message || 'Lỗi hệ thống.' });
    }
  };

  const toggleModal = () => setModalState(prev => ({ ...prev, isOpen: false }));

  let totalTicketAll = 0;
  let createdTicketAll = 0;

  const typeMetrics = TICKET_TYPES.map(type => {
    let total = ticketData[type]?.total || 0;
    let created = ticketData[type]?.created || 0;
    
    // Fallback logic for when ALL is checking and jobState updates the results incrementally
    const isThisTypeActive = activeJobType === type || activeJobType === 'ALL';
    if (jobState && isThisTypeActive && (jobState.status === 'running' || jobState.status === 'completed')) {
       // Only override if jobState provides actual results for this type
       if (jobState.results && Array.isArray(jobState.results)) {
           if (activeJobType === type) {
               total = Math.max(total, jobState.total);
               created = countCreated(jobState.results);
           }
       } else if (jobState.results && typeof jobState.results === 'object' && activeJobType === 'ALL') {
           const typeResults = jobState.results[type];
           if (typeResults && Array.isArray(typeResults)) {
               created = countCreated(typeResults);
           }
       }
    }
    
    totalTicketAll += total;
    createdTicketAll += created;
    const uncreated = Math.max(0, total - created);
    const pct = total > 0 ? Math.round((created / total) * 100) : 0;

    return { type, total, created, uncreated, pct, loading: ticketData[type]?.loading };
  });

  const overallPct = totalTicketAll > 0 ? Math.min((createdTicketAll / totalTicketAll) * 100, 100).toFixed(1) : '0.0';

  return (
    <div className="-m-6 h-[calc(100%+3rem)] flex flex-col bg-[#0B1120] text-slate-200 font-sans overflow-hidden relative">
      
      {/* HEADER */}
      <header className="flex justify-between items-center px-8 py-5 shrink-0 z-10 relative bg-slate-950/20 backdrop-blur-md border-b border-slate-800/50">
        <div>
          <h1 className="text-[13px] font-bold tracking-[0.2em] uppercase text-white">Ticket SSC</h1>
          <p className="text-[10px] text-slate-500 mt-0.5 tracking-wide">Quản lý và kiểm tra trạng thái ticket</p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Sync status badge */}
          {globalLoading ? (
            <div className="flex items-center gap-2 text-[10px] font-bold tracking-wider uppercase text-blue-400">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
              ĐANG ĐỒNG BỘ
            </div>
          ) : (
            <div className="flex items-center gap-2 text-[10px] font-bold tracking-wider uppercase text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              ĐÃ ĐỒNG BỘ
            </div>
          )}

          <div className="w-px h-6 bg-slate-800"></div>

          {/* REFRESH BUTTON */}
          <button
            onClick={() => fetchAllGSheet(0)}
            disabled={globalLoading || isRunning}
            className="px-3.5 py-2 text-[10px] font-bold tracking-wider uppercase rounded-lg border border-slate-700/50 bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center gap-1.5"
            title="Tải lại dữ liệu Google Sheets"
          >
            <svg className={`w-3.5 h-3.5 ${globalLoading ? 'animate-spin text-blue-400' : 'text-slate-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            LÀM MỚI
          </button>

          {/* CHECK ALL TICKET BUTTON */}
          <button
            onClick={() => startCheckJob('ALL')}
            disabled={isRunning || globalLoading}
            className={`px-5 py-2 text-[10px] font-bold tracking-wider uppercase rounded-lg border transition-colors flex items-center gap-2 ${
              (isRunning && activeJobType === 'ALL') 
                ? 'bg-blue-500/15 text-blue-400 border-blue-500/30 cursor-not-allowed'
                : 'bg-slate-800 hover:bg-slate-700 text-white border-slate-700/50'
            }`}
          >
            {(isRunning && activeJobType === 'ALL') ? (
              <>
                <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                ĐANG KIỂM TRA...
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                CHECK TẤT CẢ TICKET
              </>
            )}
          </button>
        </div>
      </header>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-6 relative">
        <div className="absolute top-[20%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-500/5 rounded-full blur-[120px] pointer-events-none"></div>
        
        {/* 4 SUMMARY CARDS */}
        <div className="grid grid-cols-4 gap-5 relative z-10">
          {typeMetrics.map((m, i) => (
            <div key={i} className="bg-slate-900/30 border border-slate-800/50 rounded-xl p-5 flex flex-col">
               <div className="text-[10px] font-bold tracking-[0.15em] text-white uppercase mb-5">{m.type}</div>
               
               <div className="flex items-end justify-between mb-4">
                 <div>
                   <div className="text-[9px] font-bold tracking-wider text-slate-500 uppercase mb-1">Tổng ticket</div>
                   <div className="text-3xl font-light text-white tabular-nums">
                      {m.loading ? (
                         <div className="w-12 h-9 bg-slate-800/50 animate-pulse rounded"></div>
                      ) : (
                         m.total.toLocaleString('vi-VN')
                      )}
                   </div>
                 </div>
               </div>
               
               <div className="space-y-2 text-[11px] mb-4">
                 <div className="flex justify-between">
                   <span className="text-emerald-400/80">✓ Đã tạo</span>
                   <span className="text-emerald-400 font-semibold tabular-nums">{m.loading ? '-' : m.created.toLocaleString('vi-VN')}</span>
                 </div>
                 <div className="flex justify-between">
                   <span className={m.uncreated > 0 ? "text-amber-400/80" : "text-slate-500"}>○ Chưa tạo</span>
                   <span className={m.uncreated > 0 ? "text-amber-400 font-semibold tabular-nums" : "text-slate-500 font-semibold tabular-nums"}>{m.loading ? '-' : m.uncreated.toLocaleString('vi-VN')}</span>
                 </div>
               </div>
               
               <div className="mb-2">
                 <div className="flex justify-between text-[9px] font-bold tracking-wider mb-1">
                   <span className="text-slate-600 uppercase">Progress</span>
                   <span className="text-blue-400">{m.pct}%</span>
                 </div>
                 <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                   <div className="h-full bg-blue-500 rounded-full transition-all duration-500" style={{ width: `${m.pct}%` }}></div>
                 </div>
               </div>

               {/* CREATE ACTION */}
               {m.uncreated > 0 && (
                 <button 
                   onClick={() => startJob(m.type)}
                   disabled={isRunning}
                   className="mt-4 w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold tracking-wider uppercase rounded-lg transition-colors disabled:opacity-50"
                 >
                   {isRunning && activeJobType === m.type ? 'ĐANG TẠO...' : `TẠO ${m.uncreated} TICKET`}
                 </button>
               )}
            </div>
          ))}
        </div>

        {/* GLOBAL PROGRESS */}
        <div className="flex items-center gap-6 px-1 relative z-10">
          <div className="text-[10px] font-bold tracking-[0.15em] text-slate-500 uppercase whitespace-nowrap">Tổng tiến độ</div>
          <div className="flex-1 h-1 bg-slate-800/80 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full relative transition-all duration-500" style={{ width: `${overallPct}%` }}>
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-[shimmer_2s_infinite_linear]"></div>
            </div>
          </div>
          <div className="text-sm text-white tabular-nums font-medium whitespace-nowrap">
            <span className="text-emerald-400">{createdTicketAll.toLocaleString('vi-VN')}</span>
            <span className="text-slate-600 mx-1">/</span>
            <span>{totalTicketAll.toLocaleString('vi-VN')}</span>
            <span className="text-slate-500 text-[10px] ml-2">{overallPct}%</span>
          </div>
        </div>

        {jobState?.error && (
          <div className="px-6 py-4 text-rose-400 text-sm font-medium flex items-center bg-rose-500/10 border border-rose-500/20 rounded-xl shrink-0 mt-6 relative z-10">
            <svg className="w-5 h-5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
            {jobState.error.message}
          </div>
        )}

      </div>

      {/* MODAL */}
      {modalState.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0B1120]/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl shadow-2xl max-w-md w-full mx-4">
            <h3 className={`text-lg font-bold mb-2 ${modalState.type === 'error' ? 'text-rose-400' : 'text-emerald-400'}`}>
              {modalState.title}
            </h3>
            <p className="text-slate-300 text-sm leading-relaxed mb-6">{modalState.message}</p>
            <div className="flex justify-end">
              <button
                onClick={toggleModal}
                className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-bold tracking-wide uppercase rounded border border-slate-600 transition-colors"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes shimmer {
          from { transform: translateX(-100%); }
          to { transform: translateX(200%); }
        }
      `}</style>
    </div>
  );
};

export default TicketSSC;
