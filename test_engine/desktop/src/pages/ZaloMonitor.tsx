import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  RefreshCw, Key, Trash2,
  ChevronDown, ChevronUp, CheckCircle2, X
} from 'lucide-react';
import { zaloApi } from '../api/zalo';

const HISTORY_OPTIONS = [
  { value: 3, label: '3 cuộn (Gần nhất)' },
  { value: 6, label: '6 cuộn (1-2h)' },
  { value: 12, label: '12 cuộn (Nửa ngày)' },
  { value: 20, label: '20 cuộn (Hôm qua)' },
  { value: 50, label: '50 cuộn (Nhiều ngày)' },
  { value: 100, label: '100 cuộn (Sâu nhất)' },
];

const ZaloMonitor: React.FC = () => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [batchInterval, setBatchInterval] = useState(10);
  const [selectedGroup, setSelectedGroup] = useState('');
  const [fixedGroup, setFixedGroup] = useState('');
  const [conversations, setConversations] = useState<{ id: string; name: string }[]>([]);
  const [stats, setStats] = useState({
    total_detected: 0,
    total_errors: 0,
    total_synced: 0,
    total_failed: 0,
    total_pending: 0
  });
  const [adapterStatus, setAdapterStatus] = useState<any>({});
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [historyScrolls, setHistoryScrolls] = useState(3);
  const [isHistoryDropdownOpen, setIsHistoryDropdownOpen] = useState(false);

  // UI Filters & Helpers
  const [isLogExpanded, setIsLogExpanded] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [groupSearchQuery, setGroupSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const historyDropdownRef = useRef<HTMLDivElement>(null);

  const logEndRef = useRef<HTMLDivElement>(null);

  const fetchStatus = async () => {
    try {
      // getStatus(false) tối ưu hiệu năng, không tải danh sách tin nhắn rườm rà
      const res = await zaloApi.getStatus(false);
      if (res.success && res.data) {
        setIsMonitoring(res.data.is_monitoring);
        if (res.data.batch_interval_minutes !== undefined && res.data.batch_interval_minutes !== null) {
          setBatchInterval(res.data.batch_interval_minutes);
        }
        setAdapterStatus(res.data.adapter_status || {});
        setStats(res.data.stats || { total_detected: 0, total_errors: 0, total_synced: 0, total_failed: 0, total_pending: 0 });
        setLogs(res.data.logs || []);
        if (res.data.fixed_group_name) {
          setFixedGroup(res.data.fixed_group_name);
          setSelectedGroup(res.data.fixed_group_name);
        } else if (res.data.adapter_status?.active_group) {
          setSelectedGroup(prev => prev || res.data.adapter_status.active_group);
        }
      }
    } catch (err: any) {
      if (err?.message !== 'Failed to fetch') {
        console.warn('Lỗi lấy status:', err);
      }
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchConversations();

    const statusInterval = setInterval(() => {
      fetchStatus();
    }, 10000);

    return () => {
      clearInterval(statusInterval);
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
      if (historyDropdownRef.current && !historyDropdownRef.current.contains(event.target as Node)) {
        setIsHistoryDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredConversations = useMemo(() => {
    if (!groupSearchQuery.trim()) return conversations;
    return conversations.filter(c => 
      c.name.toLowerCase().includes(groupSearchQuery.toLowerCase())
    );
  }, [conversations, groupSearchQuery]);

  useEffect(() => {
    if (isLogExpanded) {
      logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isLogExpanded]);

  const handleOpenBrowser = async (headless: boolean = false) => {
    setLoading(true);
    try {
      const res = await zaloApi.openBrowser(headless);
      setStatusMessage(res.message || (headless ? 'Zalo Web đang chạy ngầm' : 'Đã mở cửa sổ Zalo Web'));
      setTimeout(fetchConversations, 2500);
    } catch (e: any) {
      setStatusMessage('Lỗi mở trình duyệt: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseBrowser = async () => {
    setLoading(true);
    try {
      const res = await zaloApi.closeBrowser();
      setStatusMessage(res.message || 'Đã đóng trình duyệt Zalo Web');
      fetchStatus();
      setConversations([]);
    } catch (e: any) {
      setStatusMessage('Lỗi đóng trình duyệt: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchConversations = async () => {
    try {
      const res = await zaloApi.getConversations();
      if (res.success && res.data && res.data.length > 0) {
        setConversations(res.data);
        if (!selectedGroup && !fixedGroup) setSelectedGroup(res.data[0].name);
      }
    } catch (e: any) {
      // Ignored
    }
  };

  const handleSelectGroupChange = async (newGroup: string) => {
    setSelectedGroup(newGroup);
    if (newGroup.trim()) {
      try {
        setStatusMessage(`Đang chuyển sang nhóm '${newGroup}' trên Zalo Web...`);
        const res = await zaloApi.selectGroup(newGroup.trim());
        if (res.message) {
          setStatusMessage(res.message);
        }
      } catch (e: any) {
        console.warn('Lỗi chuyển nhóm tự động:', e);
      }
    }
  };

  const handleUpdateBatchInterval = async (minutes: number) => {
    const val = Math.max(1, Math.min(1440, minutes));
    setBatchInterval(val);
    try {
      const res = await zaloApi.setBatchInterval(val);
      setStatusMessage(res.message || `Đã đặt chu kỳ đồng bộ thành ${val} phút`);
    } catch (e: any) {
      console.warn('Lỗi lưu chu kỳ:', e);
    }
  };

  const handleLockGroup = async () => {
    if (!selectedGroup.trim()) {
      alert('Vui lòng chọn hoặc nhập tên Group trước khi khóa!');
      return;
    }
    setLoading(true);
    try {
      const res = await zaloApi.saveFixedGroup(selectedGroup.trim());
      setFixedGroup(selectedGroup.trim());
      setStatusMessage(res.message || 'Đã khóa cố định Group!');
      fetchStatus();
    } catch (e: any) {
      alert('Lỗi: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUnlockGroup = async () => {
    setLoading(true);
    try {
      await zaloApi.saveFixedGroup('');
      setFixedGroup('');
      setStatusMessage('Đã mở khóa nhóm. Bạn có thể chọn lại nhóm khác.');
      fetchStatus();
    } catch (e: any) {
      alert('Lỗi: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    const target = fixedGroup || selectedGroup;
    if (!target) {
      alert('Vui lòng chỉ định Group Zalo cần giám sát!');
      return;
    }
    setLoading(true);
    try {
      const res = await zaloApi.startMonitoring(target, batchInterval);
      setStatusMessage(res.message || 'Bắt đầu giám sát');
      fetchStatus();
    } catch (e: any) {
      setStatusMessage('Lỗi: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      const res = await zaloApi.stopMonitoring();
      setStatusMessage(res.message || 'Đã dừng giám sát');
      fetchStatus();
    } catch (e: any) {
      setStatusMessage('Lỗi: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScanHistory = async () => {
    const target = fixedGroup || selectedGroup;
    if (!target) {
      alert('Vui lòng chọn hoặc nhập tên Group chat trước khi quét lịch sử!');
      return;
    }
    setLoading(true);
    try {
      const res = await zaloApi.scanHistory(target, historyScrolls);
      setStatusMessage(res.message || 'Đã quét lịch sử');
      fetchStatus();
    } catch (e: any) {
      setStatusMessage('Lỗi: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncNow = async () => {
    setLoading(true);
    try {
      const res = await zaloApi.syncNow();
      setStatusMessage(res.message || 'Đã kích hoạt đồng bộ');
      fetchStatus();
    } catch (e: any) {
      setStatusMessage('Lỗi: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClearData = async () => {
    if (!window.confirm("Bạn có chắc chắn muốn XÓA TOÀN BỘ các bản quét cũ trên máy và làm sạch trang tính Google Sheets (chỉ giữ lại hàng tiêu đề) để quét mới từ đầu?")) {
      return;
    }
    setLoading(true);
    try {
      const res = await zaloApi.clearData(true, true);
      setStatusMessage(res.message || 'Đã làm sạch dữ liệu cũ thành công!');
      fetchStatus();
    } catch (e: any) {
      alert('Lỗi: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveApiKey = async () => {
    if (!apiKeyInput.trim()) return;
    try {
      const res = await zaloApi.updateGeminiKey(apiKeyInput.trim());
      alert(res.message || 'Đã lưu API Key thành công!');
      setShowKeyModal(false);
      setApiKeyInput('');
    } catch (e: any) {
      alert('Lỗi: ' + e.message);
    }
  };

  const isBrowserActive = Boolean(adapterStatus?.browser_open);
  const isBrowserLoggedIn = Boolean(adapterStatus?.logged_in);
  const isBrowserHeadless = Boolean(adapterStatus?.is_headless);

  return (
    <div className="h-full flex flex-col bg-slate-950 text-slate-100 overflow-hidden font-sans select-none">
      
      {/* 1. TOP HEADER - Tinh giản, loại bỏ icon trang trí thừa */}
      <header className="h-14 px-5 border-b border-slate-800/80 bg-slate-950 flex items-center justify-between shrink-0 z-20">
        
        {/* Left: Brand Identity + Realtime State */}
          <div className="flex items-center gap-2.5">
            <h1 className="text-sm font-bold text-white tracking-tight leading-none">
              Zalo Monitor
            </h1>
            <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide border ${
              isMonitoring 
                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' 
                : 'bg-slate-800/90 text-slate-400 border-slate-700/80'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${isMonitoring ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
              {isMonitoring ? 'ĐANG GIÁM SÁT' : 'TẠM DỪNG'}
            </span>
          </div>

        {/* Right: Master Control Actions */}
        <div className="flex items-center gap-2">
          
          {/* Zalo Browser State & Window Toggle */}
          {isBrowserActive ? (
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 shadow-sm">
              {isBrowserHeadless ? (
                <button
                  onClick={() => handleOpenBrowser(false)}
                  disabled={loading}
                  className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-sky-300 hover:text-white rounded hover:bg-slate-800 transition-colors cursor-pointer"
                  title="Zalo đang chạy ngầm. Bấm để hiển thị cửa sổ Chrome."
                >
                  <span>Hiện Zalo</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
                </button>
              ) : (
                <button
                  onClick={() => handleOpenBrowser(true)}
                  disabled={loading}
                  className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-300 hover:text-white rounded hover:bg-slate-800 transition-colors cursor-pointer"
                  title="Cửa sổ Zalo đang mở. Bấm để thu ngầm vào nền tiếp tục giám sát."
                >
                  <span>Thu ngầm</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                </button>
              )}
              <div className="w-px h-3.5 bg-slate-800 mx-0.5" />
              <button
                onClick={handleCloseBrowser}
                disabled={loading || isMonitoring}
                className="p-1 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded transition-colors cursor-pointer disabled:opacity-40"
                title="Đóng hoàn toàn trình duyệt Zalo"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => handleOpenBrowser(false)}
              disabled={loading}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-700/80 hover:border-slate-600 transition-all cursor-pointer shadow-sm disabled:opacity-50"
              title="Khởi động Zalo Web để đăng nhập và tải danh sách nhóm"
            >
              Mở Zalo Web
            </button>
          )}

          {/* Primary CTA: Bắt đầu / Dừng giám sát */}
          {!isMonitoring ? (
            <button
              onClick={handleStart}
              disabled={loading || (!fixedGroup && !selectedGroup)}
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs shadow-md shadow-emerald-950/60 transition-all disabled:opacity-40 cursor-pointer"
              title="Bắt đầu giám sát realtime nhóm Zalo"
            >
              Bắt đầu
            </button>
          ) : (
            <button
              onClick={handleStop}
              disabled={loading}
              className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs shadow-md shadow-rose-950/60 transition-all disabled:opacity-50 cursor-pointer"
              title="Dừng giám sát nhóm Zalo"
            >
              Dừng
            </button>
          )}

          {/* Cụm công cụ cài đặt phụ (Key Gemini & Clear Data) */}
          <div className="flex items-center gap-1 border-l border-slate-800 pl-2">
            <button
              onClick={() => setShowKeyModal(true)}
              className="p-1.5 text-slate-400 hover:text-amber-300 hover:bg-slate-900 rounded-lg border border-transparent hover:border-slate-800 transition-colors cursor-pointer"
              title="Cấu hình Google Gemini AI Key"
            >
              <Key className="w-4 h-4 text-amber-400" />
            </button>

            <button
              onClick={handleClearData}
              disabled={loading || isMonitoring}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 rounded-lg border border-transparent hover:border-rose-900/30 transition-colors disabled:opacity-30 cursor-pointer"
              title="Xóa toàn bộ bản ghi cũ trên máy và làm sạch trang Google Sheets"
            >
              <Trash2 className="w-4 h-4 text-rose-400" />
            </button>
          </div>

        </div>
      </header>

      {/* 2. SUB-TOOLBAR: Gọn gàng, loại bỏ các icon trang trí thừa */}
      <div className="px-5 py-2 border-b border-slate-800/60 bg-slate-900/40 flex flex-wrap items-center justify-between gap-3 shrink-0">
        
        {/* Nhóm Chat Zalo mục tiêu */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Nhóm theo dõi:
          </span>

          {fixedGroup ? (
            <div className="flex items-center gap-2 bg-slate-950 border border-emerald-500/30 rounded-lg px-2.5 py-1 text-xs">
              <span className="font-semibold text-emerald-300 max-w-[200px] truncate">{fixedGroup}</span>
              <span className="text-[9px] uppercase tracking-wider bg-emerald-500/20 text-emerald-300 px-1 py-0.2 rounded font-medium">Cố định</span>
              <button
                onClick={handleUnlockGroup}
                disabled={isMonitoring}
                className="text-slate-400 hover:text-amber-300 hover:underline text-[11px] disabled:opacity-30 cursor-pointer"
                title="Mở khóa nhóm để chọn nhóm khác"
              >
                Đổi nhóm
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 relative" ref={dropdownRef}>
              <div className="relative w-56">
                <button
                  type="button"
                  onClick={() => {
                    if (!isMonitoring) {
                      if (!isDropdownOpen && conversations.length === 0) {
                        fetchConversations();
                      }
                      setIsDropdownOpen(!isDropdownOpen);
                    }
                  }}
                  disabled={isMonitoring}
                  className="w-full flex items-center justify-between bg-slate-950 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 transition-all text-left focus:outline-none disabled:opacity-50 cursor-pointer"
                  title="Chọn Group mục tiêu"
                >
                  <span className="truncate font-medium">
                    {selectedGroup || <span className="text-slate-500 font-normal">-- Chọn Group --</span>}
                  </span>
                  <ChevronDown className={`w-3.5 h-3.5 text-slate-400 shrink-0 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {isDropdownOpen && (
                  <div className="absolute z-50 left-0 w-72 mt-1 bg-slate-950 border border-slate-800 rounded-xl shadow-2xl overflow-hidden backdrop-blur-md">
                    <div className="p-2 border-b border-slate-800 bg-slate-900/60 flex items-center gap-2">
                      <SearchInput value={groupSearchQuery} onChange={setGroupSearchQuery} />
                    </div>

                    <div className="max-h-56 overflow-y-auto divide-y divide-slate-800/40">
                      {filteredConversations.length > 0 ? (
                        filteredConversations.map((c) => {
                          const isSelected = selectedGroup === c.name;
                          return (
                            <button
                              key={c.id}
                              type="button"
                              onClick={() => {
                                handleSelectGroupChange(c.name);
                                setIsDropdownOpen(false);
                              }}
                              className={`w-full flex items-center justify-between px-3 py-1.5 text-left text-xs transition-colors cursor-pointer ${
                                isSelected ? 'bg-emerald-500/15 text-emerald-300 font-semibold' : 'text-slate-300 hover:bg-slate-900 hover:text-white'
                              }`}
                            >
                              <div className="flex items-center gap-2 truncate pr-2">
                                <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${isSelected ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                                <span className="truncate">{c.name}</span>
                              </div>
                              {isSelected && <span className="text-[9px] bg-emerald-500/20 text-emerald-300 px-1 py-0.2 rounded font-medium shrink-0">Chọn</span>}
                            </button>
                          );
                        })
                      ) : (
                        <div className="px-3 py-2 text-center text-xs text-slate-400">
                          {groupSearchQuery ? (
                            <div>
                              <span>Không có nhóm trùng.</span>
                              <button onClick={() => { handleSelectGroupChange(groupSearchQuery.trim()); setIsDropdownOpen(false); }} className="mt-1 block mx-auto text-emerald-400 hover:underline text-[11px]">
                                Dùng "{groupSearchQuery.trim()}"
                              </button>
                            </div>
                          ) : 'Chưa tải được danh sách nhóm'}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <button
                onClick={fetchConversations}
                title="Tải lại danh sách nhóm từ Zalo Web"
                className="p-1 text-slate-400 hover:text-white bg-slate-950 hover:bg-slate-900 border border-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={handleLockGroup}
                disabled={isMonitoring || !selectedGroup}
                className="px-2.5 py-1 text-xs font-medium text-emerald-400 bg-emerald-950/30 hover:bg-emerald-900/40 border border-emerald-500/30 rounded-lg transition-colors disabled:opacity-40 cursor-pointer"
                title="Khóa cố định nhóm này"
              >
                Khóa
              </button>
            </div>
          )}
        </div>

        {/* Quét tin cũ + Chu kỳ đồng bộ Sheets + Nút đẩy ngay */}
        <div className="flex items-center gap-3">
          
          {/* Cụm Quét Lịch Sử */}
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-0.5" ref={historyDropdownRef}>
            <div className="relative">
              <button
                type="button"
                onClick={() => setIsHistoryDropdownOpen(!isHistoryDropdownOpen)}
                disabled={loading}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-slate-300 hover:text-white rounded hover:bg-slate-900 transition-colors cursor-pointer disabled:opacity-50"
                title="Chọn số lượng cuộn lịch sử tin nhắn"
              >
                <span>{HISTORY_OPTIONS.find(o => o.value === historyScrolls)?.label || `${historyScrolls} cuộn`}</span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isHistoryDropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {isHistoryDropdownOpen && (
                <div className="absolute top-full mt-1.5 left-0 z-50 w-52 bg-slate-950 border border-slate-800 rounded-lg shadow-2xl py-1 overflow-hidden">
                  <div className="px-2.5 py-1 text-[10px] uppercase font-bold text-slate-500 tracking-wider border-b border-slate-800/80 mb-0.5">
                    Phạm vi cuộn lịch sử
                  </div>
                  {HISTORY_OPTIONS.map((opt) => {
                    const isSelected = historyScrolls === opt.value;
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => {
                          setHistoryScrolls(opt.value);
                          setIsHistoryDropdownOpen(false);
                        }}
                        className={`w-full text-left px-2.5 py-1.5 text-xs transition-colors flex items-center justify-between cursor-pointer ${
                          isSelected
                            ? 'bg-amber-500/15 text-amber-300 font-semibold'
                            : 'text-slate-300 hover:bg-slate-900 hover:text-white'
                        }`}
                      >
                        <span>{opt.label}</span>
                        {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0"></span>}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <button
              onClick={handleScanHistory}
              disabled={loading || (!fixedGroup && !selectedGroup)}
              className="px-2.5 py-1 rounded bg-slate-850 hover:bg-slate-800 text-slate-200 text-xs font-medium transition-all disabled:opacity-40 cursor-pointer border-l border-slate-800"
              title="Quét tin nhắn cũ trong nhóm"
            >
              Quét tin cũ
            </button>
          </div>

          <div className="h-4 w-px bg-slate-800" />

          {/* Cụm Chu kỳ đồng bộ */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Chu kỳ:
            </span>
            <select
              value={[1, 2, 5, 10, 15, 20, 30, 60].includes(batchInterval) ? batchInterval : 'custom'}
              onChange={(e) => {
                const val = e.target.value;
                if (val !== 'custom') {
                  handleUpdateBatchInterval(Number(val));
                }
              }}
              className="bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-lg px-2 py-1 text-xs font-semibold text-emerald-400 focus:outline-none cursor-pointer"
            >
              <option value={1}>1 phút</option>
              <option value={2}>2 phút</option>
              <option value={5}>5 phút</option>
              <option value={10}>10 phút</option>
              <option value={15}>15 phút</option>
              <option value={20}>20 phút</option>
              <option value={30}>30 phút</option>
              <option value={60}>60 phút</option>
              {![1, 2, 5, 10, 15, 20, 30, 60].includes(batchInterval) && (
                <option value="custom">{batchInterval} phút</option>
              )}
            </select>
          </div>

          {/* Đẩy Google Sheets ngay */}
          <button
            onClick={handleSyncNow}
            disabled={loading}
            title="Đẩy ngay các tin nhắn đang chờ lên Google Sheets"
            className="px-3 py-1 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-all disabled:opacity-40 cursor-pointer shadow-sm"
          >
            Đẩy Sheet ngay
          </button>

        </div>
      </div>

      {/* Status Alert Toast */}
      {statusMessage && (
        <div className="px-5 py-2 bg-emerald-950/30 border-b border-emerald-500/20 text-xs text-emerald-400 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-400" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage('')} className="text-emerald-400/60 hover:text-emerald-300 cursor-pointer text-xs">✕</button>
        </div>
      )}

      {/* 3. MAIN DASHBOARD CONTENT AREA */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4">
        
        {/* KPI / STATUS CARDS GRID - Thuần số liệu tinh gọn, không còn icon trang trí thừa */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          
          {/* Card 1: Tổng tin nhắn quét */}
          <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
                Tổng tin nhắn quét
              </span>
              <div className="text-2xl font-bold text-white mt-1 font-mono">
                {stats.total_detected.toLocaleString()}
              </div>
            </div>
            <span className="text-[10px] text-slate-500 truncate block mt-2">
              Nhóm: {fixedGroup || selectedGroup || 'Chưa chọn'}
            </span>
          </div>

          {/* Card 2: Sự cố phát hiện */}
          <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-medium text-amber-400/90 uppercase tracking-wider block">
                Sự cố lỗi phát hiện
              </span>
              <div className="text-2xl font-bold text-amber-300 mt-1 font-mono">
                {stats.total_errors.toLocaleString()}
              </div>
            </div>
            <span className="text-[10px] text-slate-500 block mt-2">
              Phân tích bởi Gemini AI
            </span>
          </div>

          {/* Card 3: Google Sheets Sync */}
          <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-medium text-emerald-400/90 uppercase tracking-wider block">
                Đã đẩy Google Sheets
              </span>
              <div className="text-2xl font-bold text-emerald-300 mt-1 font-mono flex items-baseline gap-1.5">
                <span>{stats.total_synced.toLocaleString()}</span>
                {stats.total_pending > 0 && (
                  <span className="text-xs font-normal text-amber-400 font-sans">
                    (+{stats.total_pending} chờ)
                  </span>
                )}
              </div>
            </div>
            <span className="text-[10px] text-slate-500 block mt-2">
              Tự động mỗi {batchInterval} phút/lần
            </span>
          </div>

          {/* Card 4: Trạng thái phiên làm việc */}
          <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-medium text-sky-400/90 uppercase tracking-wider block">
                Phiên Zalo Web
              </span>
              <div className="text-sm font-bold text-slate-200 mt-2 flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${isBrowserActive ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                <span>
                  {isBrowserActive 
                    ? (isBrowserHeadless ? 'Chạy ngầm (Headless)' : 'Cửa sổ đang mở') 
                    : 'Chưa khởi động'}
                </span>
              </div>
            </div>
            <span className="text-[10px] text-slate-500 block mt-2">
              {isBrowserLoggedIn ? 'Đã sẵn sàng quét' : 'Chờ kiểm tra đăng nhập'}
            </span>
          </div>

        </div>

        {/* 4. COLLAPSIBLE SYSTEM LOG (Gọn gàng, hiện đại) */}
        <div className="bg-slate-950 border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
          <div 
            onClick={() => setIsLogExpanded(!isLogExpanded)}
            className="px-4 py-2.5 bg-slate-900/40 hover:bg-slate-900/70 flex items-center justify-between cursor-pointer transition-colors"
          >
            <div className="flex items-center gap-2 text-xs font-mono text-slate-400 truncate">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Log hoạt động:</span>
              <span className="text-slate-300 truncate">
                {logs.length > 0 ? logs[logs.length - 1] : 'Hệ thống đang sẵn sàng.'}
              </span>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[10px] font-mono text-slate-500">{logs.length} dòng</span>
              {isLogExpanded ? (
                <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              )}
            </div>
          </div>

          {isLogExpanded && (
            <div className="p-3 text-[11px] font-mono text-slate-400 h-64 overflow-y-auto space-y-1 bg-slate-950 border-t border-slate-800/80">
              {logs.map((log, idx) => (
                <div key={idx} className="leading-relaxed hover:text-slate-200">{log}</div>
              ))}
              <div ref={logEndRef} />
            </div>
          )}
        </div>

      </div>

      {/* 5. GEMINI API KEY MODAL */}
      {showKeyModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-2">
              <Key className="w-4 h-4 text-amber-400" />
              Cấu hình Google Gemini API Key
            </h3>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Gemini API hoàn toàn <strong>miễn phí 100%</strong> (1.500 requests/ngày).
              Lấy key tại <a href="https://aistudio.google.com/" target="_blank" rel="noreferrer" className="text-blue-400 underline hover:text-blue-300">aistudio.google.com</a>.
            </p>
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder="Dán AIzaSy... API key vào đây"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 mb-4 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-mono"
            />
            <div className="flex items-center justify-end gap-2.5">
              <button
                onClick={() => setShowKeyModal(false)}
                className="px-3.5 py-1.5 text-xs rounded-lg text-slate-400 hover:text-white transition-colors cursor-pointer"
              >
                Hủy
              </button>
              <button
                onClick={handleSaveApiKey}
                className="px-4 py-1.5 text-xs rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition-colors cursor-pointer"
              >
                Lưu cấu hình
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

// Helper component cho tìm kiếm Group trong dropdown
const SearchInput: React.FC<{ value: string; onChange: (val: string) => void }> = ({ value, onChange }) => {
  return (
    <div className="flex items-center gap-2 w-full">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Tìm nhóm hoặc gõ tên mới..."
        className="w-full bg-transparent text-xs text-slate-100 placeholder-slate-500 focus:outline-none"
        autoFocus
      />
      {value && (
        <button onClick={() => onChange('')} className="text-[10px] text-slate-400 hover:text-white px-1">✕</button>
      )}
    </div>
  );
};

export default ZaloMonitor;
