import React, { useState, useEffect, useRef } from 'react';
import { useTaskContext } from '../context/TaskContext';
import { useNavigate } from 'react-router-dom';
import { cameraApi } from '../api/camera';
import { settingsApi } from '../api/settings';
import { ftelDvrApi } from '../api/ftelDvr';
import type { CameraJobState } from '../api/camera';

const LEGACY_MODES = [
  { id: 'cam_lc', label: 'Camera LC', mode: 'camera', lc: true, vaccine: false, icon: 'camera' },
  { id: 'dvr_lc', label: 'DVR LC (Monitor)', mode: 'monitor', lc: true, vaccine: false, icon: 'dvr' },
  { id: 'cam_vx', label: 'Camera VX', mode: 'camera', lc: false, vaccine: true, icon: 'camera' },
  { id: 'dvr_vx', label: 'DVR VX (Monitor)', mode: 'monitor', lc: false, vaccine: true, icon: 'dvr' },
  { id: 'ftel_lc', label: 'DVR FTEL LC', mode: 'ftel', lc: true, vaccine: false, icon: 'dvr' },
  { id: 'ftel_vx', label: 'DVR FTEL VX', mode: 'ftel', lc: false, vaccine: true, icon: 'dvr' }
];

const CheckCamera: React.FC = () => {
  const [file] = useState<File | null>(null);
  
  // Start with empty or a default selection
  const [selectedModes, setSelectedModes] = useState<string[]>(() => {
    const saved = localStorage.getItem('checkCamera_selectedModes');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return ['cam_lc'];
  });

  useEffect(() => {
    localStorage.setItem('checkCamera_selectedModes', JSON.stringify(selectedModes));
  }, [selectedModes]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const { tasks, startTask, clearTask } = useTaskContext();
  const navigate = useNavigate();
  
  const [, setError] = useState('');
  const [warehouseStatus, setWarehouseStatus] = useState<any>({ status: 'loading', count: 0, lastSync: '' });
  const [periodicSettings, setPeriodicSettings] = useState<{ enabled: boolean; interval: number }>({ enabled: false, interval: 15 });
  
  useEffect(() => {
    const fetchWarehouseStatus = async () => {
      try {
        const res = await cameraApi.getWarehouseStatus();
        if (res.success && res.data) {
          setWarehouseStatus({
            ...res.data,
            lastSync: new Date().toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' })
          });
        } else {
          setWarehouseStatus({ status: 'unavailable', count: 0 });
        }
      } catch (err) {
        setWarehouseStatus({ status: 'error', count: 0 });
      }
    };
    fetchWarehouseStatus();
    settingsApi.getSettings().then(res => {
      if (res.success && res.data?.check_cam) {
        setPeriodicSettings({
          enabled: res.data.check_cam.periodic_enabled ?? false,
          interval: res.data.check_cam.periodic_interval_minutes ?? 15
        });
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isBlocked = !file && warehouseStatus.status !== 'ready';

  const handleStart = async (procId: string) => {
    const m = LEGACY_MODES.find(x => x.id === procId);
    if (!m) return;
    if (m.mode === 'camera' && isBlocked) return;
    setError('');
    
    // Clear old task if completed/cancelled before starting new
    const oldTask = tasks[procId];
    if (oldTask && (oldTask.status === 'completed' || oldTask.status === 'cancelled' || oldTask.status === 'failed')) {
      clearTask(procId as any);
    }
    
    let res;
    if (m.mode === 'ftel') {
      res = await ftelDvrApi.createJob(file, { vaccine: m.vaccine, lc: m.lc, mode: 'monitor' });
    } else {
      res = await cameraApi.createJob(file, {
        vaccine: m.vaccine,
        lc: m.lc,
        mode: m.mode,
        periodic: periodicSettings.enabled,
        interval_minutes: periodicSettings.interval
      });
    }
    if (res.success && res.data) {
      startTask(procId as any, res.data.job_id, { mode: m.mode });
    } else {
      setError(res.message || 'Lỗi khởi tạo tiến trình.');
    }
  };

  const handleStop = async (procId: string) => {
    const task = tasks[procId];
    if (task?.jobId) {
      const m = LEGACY_MODES.find(x => x.id === procId);
      if (m?.mode === 'ftel') {
        await ftelDvrApi.cancelJob(task.jobId);
      } else {
        await cameraApi.cancelJob(task.jobId);
      }
    }
  };

  const handleExport = async (procId: string) => {
    const task = tasks[procId];
    if (!task?.jobId) return;
    try {
      const m = LEGACY_MODES.find(x => x.id === procId);
      const isFtel = m?.mode === 'ftel';
      let blob;
      if (isFtel) {
        blob = await ftelDvrApi.exportJob(task.jobId);
      } else {
        blob = await cameraApi.exportJob(task.jobId);
      }
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${isFtel ? 'DVR_FTEL' : 'Camera_Result'}_${procId}_${new Date().getTime()}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e: any) {
      alert("Lỗi export: " + e.message);
    }
  };

  const handleSync = async (procId: string) => {
    const task = tasks[procId];
    if (!task?.jobId) return;
    try {
      const res = await cameraApi.syncJob(task.jobId);
      if (res.success) {
        alert("Đồng bộ thành công!");
      } else {
        alert("Lỗi đồng bộ: " + res.message);
      }
    } catch (e: any) {
      alert("Lỗi đồng bộ: " + e.message);
    }
  };

  const handleSkipWait = async (procId: string) => {
    const task = tasks[procId];
    if (!task?.jobId) return;
    try {
      await cameraApi.skipWait(task.jobId);
    } catch (e: any) {
      console.error("Lỗi bỏ qua chờ:", e);
    }
  };

  const toggleMode = (id: string) => {
    setSelectedModes(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const activeWaitingTask = Object.values(tasks).find(t => t?.jobState?.cycle_status === 'waiting');
  const waitingJobState = activeWaitingTask?.jobState;

  const displayedProcs = LEGACY_MODES.filter(m => selectedModes.includes(m.id));
  const gridCols = displayedProcs.length === 1 ? 'grid-cols-1 max-w-md' :
                   displayedProcs.length === 2 ? 'grid-cols-2' :
                   displayedProcs.length === 3 ? 'grid-cols-3' : 'grid-cols-4';

  return (
    <div className="-m-6 h-[calc(100%+3rem)] flex flex-col bg-[#0B1120] text-slate-200 font-sans overflow-hidden">
      
      {/* 1. TOP CONTROL BAR */}
      <header className="h-20 border-b border-slate-800/60 flex items-center justify-between px-10 shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-slate-100 tracking-tight">Check Camera</h1>
          <div className="text-[11px] text-slate-500 font-medium uppercase tracking-widest mt-1">Device Monitoring</div>
        </div>
        
        <div className="flex items-center gap-3">
          {waitingJobState && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-bold rounded-lg animate-pulse shadow-sm">
              <svg className="w-4 h-4 text-amber-400 animate-spin" style={{ animationDuration: '6s' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Chu kỳ #{(waitingJobState.cycle || 1) + 1} sau:</span>
              <span className="font-mono text-sm tracking-wider font-black text-amber-200">
                {Math.floor((waitingJobState.next_cycle_seconds || 0) / 60).toString().padStart(2, '0')}:
                {((waitingJobState.next_cycle_seconds || 0) % 60).toString().padStart(2, '0')}
              </span>
            </div>
          )}

          {/* Quick Periodic Scan Control */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/60 border border-slate-800 rounded-lg text-xs">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={periodicSettings.enabled}
                onChange={async (e) => {
                  const enabled = e.target.checked;
                  setPeriodicSettings(prev => ({ ...prev, enabled }));
                  try {
                    await settingsApi.updateSettings({
                      check_cam: {
                        periodic_enabled: enabled,
                        periodic_interval_minutes: periodicSettings.interval
                      }
                    });
                  } catch (err) {}
                }}
                className="w-3.5 h-3.5 rounded border-slate-600 bg-slate-950 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-900"
              />
              <span className={`font-medium ${periodicSettings.enabled ? 'text-blue-400' : 'text-slate-400'}`}>
                Quét chu kỳ
              </span>
            </label>

            {periodicSettings.enabled && (
              <div className="flex items-center gap-1.5 pl-2 border-l border-slate-700/60">
                <span className="text-slate-500">Nghỉ:</span>
                <select
                  value={periodicSettings.interval}
                  onChange={async (e) => {
                    const interval = parseInt(e.target.value, 10);
                    setPeriodicSettings(prev => ({ ...prev, interval }));
                    try {
                      await settingsApi.updateSettings({
                        check_cam: {
                          periodic_enabled: periodicSettings.enabled,
                          periodic_interval_minutes: interval
                        }
                      });
                    } catch (err) {}
                  }}
                  className="bg-slate-950 border border-slate-700 rounded px-1.5 py-0.5 text-xs text-blue-300 font-medium outline-none cursor-pointer"
                >
                  <option value={5}>5 phút</option>
                  <option value={10}>10 phút</option>
                  <option value={15}>15 phút</option>
                  <option value={30}>30 phút</option>
                  <option value={60}>60 phút</option>
                  <option value={120}>2 giờ</option>
                </select>
                <span className="text-[10px] text-emerald-400 font-medium ml-1">● Tự đồng bộ GSheet</span>
              </div>
            )}
          </div>
          <div className="relative" ref={dropdownRef}>
            <button 
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="h-9 px-4 bg-slate-900/40 border border-slate-800/60 hover:bg-slate-800/40 rounded-lg text-sm text-slate-300 outline-none cursor-pointer transition-colors flex items-center gap-2"
            >
              Select Processes
              <svg className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>
            </button>
            
            {isDropdownOpen && (
              <div className="absolute right-0 top-full mt-2 w-56 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden z-50">
                <div className="p-2 flex flex-col">
                  {LEGACY_MODES.map(mode => (
                    <label key={mode.id} className="flex items-center gap-3 px-3 py-2 hover:bg-slate-700/50 rounded cursor-pointer transition-colors">
                      <input 
                        type="checkbox" 
                        className="w-4 h-4 rounded border-slate-600 bg-slate-900 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-800"
                        checked={selectedModes.includes(mode.id)}
                        onChange={() => toggleMode(mode.id)}
                      />
                      <span className="text-sm font-medium text-slate-200">{mode.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 2. PROCESS GRID */}
      <div className="flex-1 overflow-y-auto px-10 py-10">
        <style>{`
          .tabular-nums { font-variant-numeric: tabular-nums; }
          @keyframes pulse-dot { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.9); } }
          .animate-pulse-dot { animation: pulse-dot 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
          @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(200%); } }
          .animate-shimmer::after {
            content: ''; position: absolute; top: 0; left: 0; width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 1.5s infinite linear;
          }
        `}</style>

        {displayedProcs.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-slate-500 text-sm">Select processes to start monitoring</div>
          </div>
        ) : (
          <div className={`grid ${gridCols} gap-8 items-start`}>
            {displayedProcs.map(proc => {
              const cardTask = tasks[proc.id];
              const cardJobState = cardTask as any as CameraJobState;
              
              let status = 'IDLE';
              let progressPct = 0;
              let processed = 0;
              let total = 0;
              let detected = 0;
              
              let online = 0;
              let offline = 0;
              let errorCount = 0;

              let dvrErrorCount = 0;
              let dvrOfflineCount = 0;

              if (cardJobState) {
                if (cardJobState.status === 'completed') status = 'COMPLETED';
                else if (cardJobState.status === 'failed') status = 'FAILED';
                else if (cardJobState.status === 'cancelled') status = 'CANCELLED';
                else if (cardJobState.status === 'queued') status = 'QUEUED';
                else status = 'RUNNING';

                total = cardJobState.total || 0;
                processed = cardJobState.progress || 0;
                progressPct = total > 0 ? Math.min((processed / total) * 100, 100) : 0;
                
                const newErrs = cardJobState.metrics?.new_errors || 0;
                const oldErrs = cardJobState.metrics?.total_old_errors || 0;
                detected = newErrs + oldErrs;

                const anyMetrics = cardJobState.metrics as any;
                online = anyMetrics?.online || 0; 
                offline = anyMetrics?.offline || 0;
                errorCount = newErrs;
                
                if(online === 0 && processed > 0) {
                   online = processed - offline - errorCount;
                   if(online < 0) online = 0;
                }
                
                if (proc.mode === 'monitor') {
                  const resArr = cardJobState.results || [];
                  const uniqueSet = new Map();
                  resArr.forEach((r: any) => {
                     const key = r["Mã shop"] || r["IP"] || Math.random().toString();
                     uniqueSet.set(key, r["Kết quả"]);
                  });
                  uniqueSet.forEach((val) => {
                     if (val === "Lỗi Đầu Ghi" || val === "Lỗi Đầu ghi") dvrErrorCount++;
                     else if (val === "Offline") dvrOfflineCount++;
                  });
                  detected = dvrErrorCount + dvrOfflineCount;
                }
              }

              const isRunning = status === 'RUNNING' || status === 'QUEUED';
              const isCompleted = status === 'COMPLETED';
              const canExport = (status === 'COMPLETED' || status === 'CANCELLED' || status === 'FAILED') && (processed > 0);
              
              let cardClasses = "bg-slate-900/30 border rounded-2xl p-7 flex flex-col min-h-[300px] transition-all duration-300 ";
              let iconColor = "text-slate-400";
              let titleColor = "text-slate-300";
              let badgeClasses = "bg-slate-800/30 border-slate-700/50 text-slate-400";
              let dotClasses = "bg-slate-500";
              let pctColor = "text-slate-500";
              let barBgColor = "bg-slate-600";
              let detectedValColor = "text-slate-400";

              if (isRunning) {
                cardClasses += "border-blue-500/30 shadow-[0_0_12px_rgba(59,130,246,0.06)] opacity-100 scale-[1.01]";
                iconColor = "text-blue-400";
                titleColor = "text-slate-100";
                badgeClasses = "bg-blue-500/10 border-blue-500/20 text-blue-400";
                dotClasses = "bg-blue-400 animate-pulse-dot";
                pctColor = "text-blue-400";
                barBgColor = "bg-blue-500 animate-shimmer relative";
                detectedValColor = "text-slate-100";
              } else if (isCompleted) {
                cardClasses += "border-slate-800/40 shadow-sm opacity-100";
                iconColor = "text-emerald-400";
                titleColor = "text-slate-100";
                badgeClasses = "bg-emerald-500/10 border-emerald-500/20 text-emerald-400";
                pctColor = "text-emerald-400";
                barBgColor = "bg-emerald-500";
                detectedValColor = "text-slate-200";
              } else {
                cardClasses += "border-slate-800/40 opacity-75 shadow-sm";
              }

              return (
                <div key={proc.id} className={cardClasses + " cursor-pointer hover:border-slate-700/80"} onDoubleClick={() => navigate("/all-shop")}>
                  <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-3">
                      <span className={iconColor}>
                        {proc.icon === 'camera' ? (
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/></svg>
                        )}
                      </span>
                      <span className={`text-base font-semibold ${titleColor}`}>{proc.label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {cardJobState?.cycle && cardJobState.cycle > 0 ? (
                        cardJobState.cycle_status === 'waiting' ? (
                          <div className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-bold rounded-lg bg-amber-500/15 border border-amber-500/40 text-amber-300 shadow-sm animate-pulse">
                            <svg className="w-3.5 h-3.5 text-amber-400 animate-spin" style={{ animationDuration: '6s' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>Vòng #{(cardJobState.cycle || 1) + 1} sau:</span>
                            <span className="font-mono text-xs font-black tracking-wider text-amber-200">
                              {Math.floor((cardJobState.next_cycle_seconds || 0) / 60).toString().padStart(2, '0')}:
                              {((cardJobState.next_cycle_seconds || 0) % 60).toString().padStart(2, '0')}
                            </span>
                          </div>
                        ) : (
                          <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded bg-slate-800 text-blue-300 border border-slate-700">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping"></span>
                            Chu kỳ #{cardJobState.cycle}
                          </span>
                        )
                      ) : null}
                      <span className={`px-2.5 py-1 text-[10px] uppercase font-bold tracking-wider rounded-md border flex items-center gap-1.5 ${
                        cardJobState?.cycle_status === 'waiting'
                          ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                          : badgeClasses
                      }`}>
                      {cardJobState?.cycle_status === 'waiting' ? (
                        <>
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span>
                          ĐANG NGHỈ
                        </>
                      ) : isCompleted ? (
                        <>
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7"/></svg>
                          {status}
                        </>
                      ) : (
                        <>
                          <span className={`w-1.5 h-1.5 rounded-full ${dotClasses}`}></span>
                          {status}
                        </>
                      )}
                    </span>
                    </div>
                  </div>

                  <div className="flex justify-between items-end mb-3">
                    <div className={`text-3xl font-light tracking-tight tabular-nums ${pctColor}`}>{progressPct.toFixed(0)}%</div>
                    <div className="text-sm font-medium text-slate-500 mb-1 tabular-nums">
                      {processed.toLocaleString('vi-VN')} <span className="text-slate-600 font-normal">/ {total.toLocaleString('vi-VN')}</span>
                    </div>
                  </div>
                  
                  <div className="w-full h-[4px] bg-slate-800/60 rounded-full overflow-hidden mb-8">
                    <div className={`h-full ${barBgColor} transition-all duration-300 rounded-full`} style={{ width: `${progressPct}%` }}></div>
                  </div>

                  {cardJobState?.cycle_status === 'waiting' && (
                    <div className="relative overflow-hidden bg-gradient-to-br from-amber-950/40 via-slate-900/80 to-slate-900/60 border border-amber-500/30 rounded-xl p-4 mb-5 shadow-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-9 h-9 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
                            <svg className="w-5 h-5 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                          <div>
                            <div className="text-[11px] font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                              <span>Đồng hồ đếm ngược</span>
                              <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-200 rounded text-[9px] font-mono">
                                VÒNG #{(cardJobState.cycle || 1) + 1}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400">
                              Vòng #{cardJobState.cycle} hoàn tất • Sẽ tự động quét tiếp sau:
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="font-mono text-2xl font-black text-amber-300 tracking-wider">
                            {Math.floor((cardJobState.next_cycle_seconds || 0) / 60).toString().padStart(2, '0')}
                            <span className="animate-pulse text-amber-400">:</span>
                            {((cardJobState.next_cycle_seconds || 0) % 60).toString().padStart(2, '0')}
                          </div>
                          <div className="text-[9px] text-slate-500 font-medium uppercase tracking-wider">phút : giây</div>
                        </div>
                      </div>

                      {/* Rest progress bar */}
                      {cardJobState.wait_total_seconds && cardJobState.wait_total_seconds > 0 && (
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mb-3">
                          <div
                            className="h-full bg-gradient-to-r from-amber-500 to-amber-300 transition-all duration-1000 rounded-full"
                            style={{
                              width: `${Math.min(100, Math.max(0, ((cardJobState.wait_total_seconds - (cardJobState.next_cycle_seconds || 0)) / cardJobState.wait_total_seconds) * 100))}%`
                            }}
                          />
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
                        <span className="text-[10px] text-slate-400">
                          Nghỉ {Math.round((cardJobState.wait_total_seconds || 900) / 60)} phút giữa các chu kỳ
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSkipWait(proc.id);
                          }}
                          className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-200 text-xs font-medium rounded-md transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm"
                          title="Bỏ qua thời gian nghỉ và bắt đầu chu kỳ tiếp theo ngay lập tức"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                          </svg>
                          Quét ngay
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-between items-center text-sm border-b border-slate-800/40 pb-4 mb-4">
                    <span className="text-slate-500 font-medium uppercase tracking-widest text-[11px]">{proc.mode === 'monitor' ? 'Errors Detected' : 'Detected'}</span>
                    <span className={`font-semibold text-lg tabular-nums transition-colors duration-300 ${detectedValColor}`}>
                      {detected.toLocaleString('vi-VN')}
                    </span>
                  </div>

                  {cardJobState?.last_sync_time && (
                    <div className={`flex items-center justify-between text-[11px] rounded-lg px-2.5 py-1.5 mb-4 ${
                      cardJobState.last_sync_status === 'error'
                        ? 'bg-red-500/10 border border-red-500/30 text-red-400'
                        : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                    }`}>
                      <span className="flex items-center gap-1.5 font-medium">
                        {cardJobState.last_sync_status === 'error' ? (
                          <svg className="w-3.5 h-3.5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        ) : (
                          <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" /></svg>
                        )}
                        {cardJobState.last_sync_status === 'error' ? 'Lỗi đồng bộ GSheet' : 'Đã tự động đồng bộ GSheet'}
                      </span>
                      <span className="text-slate-400 font-mono text-[10px]">{cardJobState.last_sync_time}</span>
                    </div>
                  )}

                  {proc.mode === 'camera' ? (
                    <div className="grid grid-cols-2 gap-4 mt-auto mb-6">
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Online</div>
                        <div className={`tabular-nums ${isRunning || isCompleted ? 'text-emerald-400 font-medium' : 'text-slate-400'}`}>{online.toLocaleString('vi-VN')}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Offline</div>
                        <div className={`tabular-nums ${isRunning || isCompleted ? 'text-red-400 font-medium' : 'text-slate-400'}`}>{offline.toLocaleString('vi-VN')}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Error</div>
                        <div className={`tabular-nums ${isRunning || isCompleted ? 'text-amber-400 font-medium' : 'text-slate-400'}`}>{errorCount.toLocaleString('vi-VN')}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Chập chờn</div>
                        <div className={`tabular-nums ${(cardJobState?.metrics?.recovered_count || 0) > 0 ? 'text-cyan-400 font-bold' : 'text-slate-400'}`}>
                          {((cardJobState?.metrics?.recovered_count || 0)).toLocaleString('vi-VN')}
                        </div>
                      </div>
                      <div className="col-span-2 pt-1 border-t border-slate-800/30 flex justify-between items-center">
                        <span className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Total Devices</span>
                        <span className={`tabular-nums ${isRunning || isCompleted ? 'text-slate-300 font-medium' : 'text-slate-400'}`}>{total.toLocaleString('vi-VN')}</span>
                      </div>
                    </div>
                  ) : proc.mode === 'monitor' ? (
                    <div className="mt-auto mb-6">
                      <div className="grid grid-cols-2 gap-4 mb-4 pt-1">
                        <div>
                          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Đầu ghi lỗi</div>
                          <div className={`tabular-nums ${isRunning || isCompleted ? 'text-amber-400 font-medium' : 'text-slate-400'}`}>{dvrErrorCount.toLocaleString('vi-VN')}</div>
                        </div>
                        <div>
                          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-1">Mất mạng</div>
                          <div className={`tabular-nums ${isRunning || isCompleted ? 'text-red-400 font-medium' : 'text-slate-400'}`}>{dvrOfflineCount.toLocaleString('vi-VN')}</div>
                        </div>
                      </div>
                      <div className="text-xs text-slate-600 italic text-center">
                        {isRunning ? 'Scanning active...' : (status === 'CANCELLED' ? `Monitor process stopped (${processed}/${total})` : isCompleted ? 'Monitor process finished' : 'Monitor process ready')}
                      </div>
                    </div>
                  ) : (
                    <div className="mt-auto mb-6 text-xs text-slate-600 italic text-center py-4">
                      {isRunning ? 'Scanning active...' : (status === 'CANCELLED' ? `Scan process stopped (${processed}/${total})` : isCompleted ? 'Scan process finished' : 'Scan process ready')}
                    </div>
                  )}

                                    {/* RESULT ACTIONS */}
                  {canExport && (
                    <div className="flex gap-2 mt-auto mb-4">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleExport(proc.id); }}
                        className="flex-1 h-8 flex items-center justify-center gap-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 rounded-md text-xs font-semibold transition-colors"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                        Export
                      </button>
                      {proc.mode === 'camera' && (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleSync(proc.id); }}
                          className="flex-1 h-8 flex items-center justify-center gap-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 rounded-md text-xs font-semibold transition-colors"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"/></svg>
                          Sync
                        </button>
                      )}
                    </div>
                  )}

                  {/* CONTROL BUTTON */}
                  <div className="mt-auto pt-4 border-t border-slate-800/40">
                    {isRunning ? (
                      <button 
                        onClick={() => handleStop(proc.id)}
                        className="w-full h-9 flex items-center justify-center gap-2 bg-slate-800/80 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 hover:text-red-400 text-slate-300 text-sm font-medium rounded-lg transition-colors"
                      >
                        <span className="w-2.5 h-2.5 bg-current rounded-sm"></span>
                        Stop
                      </button>
                    ) : (
                      <button 
                        onClick={() => handleStart(proc.id)}
                        disabled={proc.mode === 'camera' ? isBlocked : false}
                        className="w-full h-9 flex items-center justify-center gap-2 bg-blue-600/10 hover:bg-blue-600 hover:text-white border border-blue-500/20 text-blue-400 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
                      >
                        {status === 'COMPLETED' || status === 'FAILED' ? (
                          <>
                            <svg className="w-4 h-4 text-blue-500 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                            {status === 'COMPLETED' ? 'Run Again' : 'Retry'}
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4 text-blue-500 group-hover:text-white transition-colors" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                            Start
                          </>
                        )}
                      </button>
                    )}
                  </div>

                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default CheckCamera;
