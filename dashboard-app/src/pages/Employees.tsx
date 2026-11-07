import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { 
  Search, Plus, Edit2, MoveRight, ShieldAlert, X, Users, Calendar, 
  ExternalLink, Copy, Check, Upload, ChevronLeft, ChevronRight, 
  FileSpreadsheet, KeyRound, LogOut, RefreshCw, Sparkles, Filter, AppWindow
} from 'lucide-react';
import { EmployeeService } from '../services/employeeService';
import { ScheduleService } from '../services/scheduleService';
import type { Employee, Chain, MonthlyScheduleLink, SharePointAuthStatus, ScheduleMatrixData } from '../types';
import { GlassCard } from '../components/common/GlassCard';
import { useSidebar } from '../components/layout/Layout';

const CHAINS: Chain[] = ['FPT Shop', 'Long Châu', 'Vaccine'];

const Employees: React.FC = () => {
  const { isCollapsed } = useSidebar();
  // Sub-tabs: 'employees' | 'schedule'
  const [activeTab, setActiveTab] = useState<'employees' | 'schedule'>('employees');

  // Employee list state
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [search, setSearch] = useState('');
  const [chainFilter, setChainFilter] = useState<Chain | 'All'>('All');
  const [statusFilter, setStatusFilter] = useState<'All' | 'Active' | 'Inactive'>('All');
  const [sortBy, setSortBy] = useState<'insideCode' | 'name' | 'id' | 'chain' | 'status' | 'startDate'>('insideCode');
  
  // Modals for Employees
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isMoveModalOpen, setIsMoveModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  
  // Form State for Employee
  const [formData, setFormData] = useState({
    id: '',
    insideCode: '',
    name: '',
    chain: 'FPT Shop' as Chain,
    position: '',
    status: 'Active' as 'Active' | 'Inactive',
    startDate: ''
  });
  const [formError, setFormError] = useState('');
  const [moveTarget, setMoveTarget] = useState<Chain>('FPT Shop');

  // ─── Shift Schedule State ──────────────────────────────────────────────────
  const [selectedMonth, setSelectedMonth] = useState('2026-11');
  const [scheduleLink, setScheduleLink] = useState<MonthlyScheduleLink | null>(null);
  const [authStatus, setAuthStatus] = useState<SharePointAuthStatus>({ authenticated: false, status: 'STOPPED' });
  const [matrixData, setMatrixData] = useState<ScheduleMatrixData | null>(null);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [matrixChainFilter, setMatrixChainFilter] = useState<Chain | 'All'>('All');
  const [matrixSearch, setMatrixSearch] = useState('');
  const [copied, setCopied] = useState(false);

  // Schedule Modals
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [linkFormData, setLinkFormData] = useState({
    month: '2026-11',
    sharepointUrl: '',
    title: '',
    note: ''
  });
  const [linkFormError, setLinkFormError] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Date range filter: 'all' | 'w1' | 'w2' | 'w3' | 'w4'
  const [dateRangeFilter, setDateRangeFilter] = useState<'all' | 'w1' | 'w2' | 'w3' | 'w4'>('all');
  const tableContainerRef = React.useRef<HTMLDivElement>(null);

  const scrollTable = (direction: 'left' | 'right' | 'start' | 'end') => {
    if (!tableContainerRef.current) return;
    if (direction === 'start') {
      tableContainerRef.current.scrollTo({ left: 0, behavior: 'smooth' });
    } else if (direction === 'end') {
      tableContainerRef.current.scrollTo({ left: tableContainerRef.current.scrollWidth, behavior: 'smooth' });
    } else {
      const offset = direction === 'left' ? -380 : 380;
      tableContainerRef.current.scrollBy({ left: offset, behavior: 'smooth' });
    }
  };

  // Initial load
  useEffect(() => {
    EmployeeService.getEmployees().then(data => {
      setEmployees(data);
      setLoading(false);
    });
  }, []);

  // Load schedule data when schedule tab is opened or month changes
  useEffect(() => {
    if (activeTab === 'schedule') {
      loadScheduleData(selectedMonth);
      checkAuthStatus();
    }
  }, [activeTab, selectedMonth, matrixChainFilter]);

  const loadScheduleData = async (month: string) => {
    setScheduleLoading(true);
    try {
      const link = await ScheduleService.getScheduleLinks(month) as MonthlyScheduleLink | null;
      setScheduleLink(link);
      if (link) {
        setLinkFormData({
          month: link.month,
          sharepointUrl: link.sharepointUrl,
          title: link.title || '',
          note: link.note || ''
        });
      } else {
        setLinkFormData({
          month,
          sharepointUrl: '',
          title: `Lịch làm việc Tháng ${month.split('-')[1]}/${month.split('-')[0]}`,
          note: ''
        });
      }

      const matrix = await ScheduleService.getShiftMatrix(month, matrixChainFilter);
      setMatrixData(matrix);
    } catch (e) {
      console.error("Error loading schedule data:", e);
    } finally {
      setScheduleLoading(false);
    }
  };

  const checkAuthStatus = async () => {
    try {
      const status = await ScheduleService.getSharePointAuthStatus();
      setAuthStatus(status);
    } catch (e) {
      console.error("Error checking auth status:", e);
    }
  };

  const handleMonthChange = (offset: number) => {
    const parts = selectedMonth.split('-');
    let year = parseInt(parts[0], 10);
    let month = parseInt(parts[1], 10) + offset;
    if (month > 12) {
      month = 1;
      year += 1;
    } else if (month < 1) {
      month = 12;
      year -= 1;
    }
    const newMonthStr = `${year}-${String(month).padStart(2, '0')}`;
    setSelectedMonth(newMonthStr);
  };

  const formatMonthTitle = (monthStr: string) => {
    const parts = monthStr.split('-');
    if (parts.length === 2) {
      return `Tháng ${parts[1]} / ${parts[0]}`;
    }
    return monthStr;
  };

  const handleCopyLink = () => {
    if (scheduleLink?.sharepointUrl) {
      navigator.clipboard.writeText(scheduleLink.sharepointUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleOpenSharePointTab = () => {
    if (scheduleLink?.sharepointUrl) {
      window.open(scheduleLink.sharepointUrl, '_blank', 'noopener,noreferrer');
    }
  };

  const handleOpenParallelWindow = () => {
    if (scheduleLink?.sharepointUrl) {
      window.open(
        scheduleLink.sharepointUrl,
        'SharePointScheduleWindow',
        'width=1240,height=820,left=100,top=80,resizable=yes,scrollbars=yes'
      );
    }
  };

  const handleSaveLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setLinkFormError('');
    if (!linkFormData.sharepointUrl.trim()) {
      setLinkFormError('Vui lòng nhập đường link SharePoint');
      return;
    }
    try {
      const saved = await ScheduleService.saveScheduleLink({
        month: linkFormData.month,
        sharepointUrl: linkFormData.sharepointUrl.trim(),
        title: linkFormData.title.trim() || undefined,
        note: linkFormData.note.trim() || undefined
      });
      setScheduleLink(saved);
      setIsLinkModalOpen(false);
      loadScheduleData(selectedMonth);
    } catch (err: any) {
      setLinkFormError(err.message || 'Lỗi khi lưu liên kết');
    }
  };

  const handleStartAuthSession = async () => {
    try {
      const res = await ScheduleService.startSharePointAuth(scheduleLink?.sharepointUrl);
      setAuthStatus(res);
      // Poll a few times
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        const s = await ScheduleService.getSharePointAuthStatus();
        setAuthStatus(s);
        if (s.authenticated || attempts > 15) {
          clearInterval(interval);
        }
      }, 2000);
    } catch (e: any) {
      alert(e.message || 'Lỗi khi mở phiên đăng nhập');
    }
  };

  const handleLogoutAuthSession = async () => {
    if (window.confirm('Bạn có chắc muốn đăng xuất phiên Mail công ty và xóa cookie?')) {
      await ScheduleService.logoutSharePointAuth();
      setAuthStatus({ authenticated: false, status: 'STOPPED' });
    }
  };

  const handleImportExcelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setIsUploading(true);
    setUploadSuccess(null);
    try {
      const res = await ScheduleService.importShiftExcel(uploadFile, selectedMonth);
      setUploadSuccess(`Đã nạp thành công ${res.importedCount} lượt ca của ${res.employeesCount} nhân viên!`);
      setTimeout(() => {
        setIsUploadModalOpen(false);
        setUploadFile(null);
        setUploadSuccess(null);
        loadScheduleData(selectedMonth);
      }, 1500);
    } catch (err: any) {
      alert(err.message || 'Lỗi khi nạp file Excel');
    } finally {
      setIsUploading(false);
    }
  };

  // Helper: update a single employee in local state without reloading the whole list
  const updateLocalEmployee = (updated: Employee) => {
    setEmployees(prev => prev.map(e => e.id === updated.id ? updated : e));
  };

  const filteredEmployees = employees.filter(emp => {
    if (chainFilter !== 'All' && emp.chain !== chainFilter) return false;
    if (statusFilter !== 'All' && emp.status !== statusFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      const matchName = emp.name.toLowerCase().includes(q);
      const matchId = emp.id.toLowerCase().includes(q);
      const matchInside = (emp.insideCode || '').toLowerCase().includes(q);
      if (!matchName && !matchId && !matchInside) return false;
    }
    return true;
  }).sort((a, b) => {
    if (sortBy === 'insideCode') {
      const numA = parseInt(a.insideCode || '0', 10);
      const numB = parseInt(b.insideCode || '0', 10);
      if (!isNaN(numA) && !isNaN(numB) && numA > 0 && numB > 0) {
        return numA - numB;
      }
      return (a.insideCode || '').localeCompare(b.insideCode || '');
    }
    if (sortBy === 'name') return a.name.localeCompare(b.name);
    if (sortBy === 'id') return a.id.localeCompare(b.id);
    if (sortBy === 'chain') return a.chain.localeCompare(b.chain);
    if (sortBy === 'status') return a.status.localeCompare(b.status);
    if (sortBy === 'startDate') return (a.startDate || '').localeCompare(b.startDate || '');
    return 0;
  });

  const metrics = {
    total: employees.length,
    fpt: employees.filter(e => e.chain === 'FPT Shop').length,
    longchau: employees.filter(e => e.chain === 'Long Châu').length,
    vaccine: employees.filter(e => e.chain === 'Vaccine').length,
    active: employees.filter(e => e.status === 'Active').length,
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    if (!formData.id || !formData.name || !formData.chain) {
      setFormError('Vui lòng điền đầy đủ các trường bắt buộc');
      return;
    }
    try {
      const newEmp = await EmployeeService.createEmployee(formData);
      setEmployees(prev => [newEmp, ...prev]);
      setIsAddModalOpen(false);
      setFormData({ id: '', insideCode: '', name: '', chain: 'FPT Shop', position: '', status: 'Active', startDate: '' });
    } catch (err: any) {
      setFormError(err.message || 'Lỗi khi thêm nhân viên');
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmployee) return;
    try {
      const updated = await EmployeeService.updateEmployee({
        ...selectedEmployee,
        insideCode: formData.insideCode,
        name: formData.name, position: formData.position, status: formData.status, startDate: formData.startDate
      });
      updateLocalEmployee(updated);
      setIsEditModalOpen(false);
      setSelectedEmployee(null);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleMoveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmployee) return;
    try {
      const updated = await EmployeeService.moveEmployee(selectedEmployee.id, moveTarget);
      updateLocalEmployee(updated);
      setIsMoveModalOpen(false);
      setSelectedEmployee(null);
    } catch (err: any) {
      alert(err.message);
    }
  };

  // Shift badge color helper matching exact screenshot
  const getShiftBadgeClass = (shift: string) => {
    if (!shift) return 'text-slate-300';
    const s = shift.trim().toLowerCase();
    if (s.includes('sáng + đêm')) {
      return 'bg-indigo-100 text-indigo-800 border border-indigo-300 font-bold';
    }
    if (s.includes('trực đêm') || s.includes('đêm')) {
      return 'bg-amber-100 text-amber-800 border border-amber-300 font-bold';
    }
    if (s.includes('ca sáng') || s === 'sáng') {
      return 'bg-sky-100 text-sky-800 border border-sky-200 font-semibold';
    }
    if (s.includes('ca chiều') || s === 'chiều') {
      return 'bg-teal-100 text-teal-800 border border-teal-200 font-semibold';
    }
    if (s.includes('phép')) {
      return 'bg-rose-100 text-rose-700 border border-rose-200 font-semibold';
    }
    if (s.includes('off bù')) {
      return 'bg-slate-200 text-slate-700 border border-slate-300 font-medium';
    }
    if (s.includes('off')) {
      return 'bg-slate-100 text-slate-500 border border-slate-200 font-medium';
    }
    return 'bg-slate-100 text-slate-700 border border-slate-200';
  };

  // Filter matrix employees
  const filteredMatrixEmployees = (matrixData?.employees || []).filter(emp => {
    if (matrixChainFilter !== 'All' && emp.chain !== matrixChainFilter) return false;
    if (matrixSearch) {
      const q = matrixSearch.toLowerCase();
      if (!emp.name.toLowerCase().includes(q) && !emp.id.toLowerCase().includes(q) && !(emp.code || '').includes(q)) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className={`w-full ${isCollapsed ? 'px-3.5 sm:px-6 py-3 sm:py-4' : 'px-3.5 sm:px-6 lg:px-12 py-4 sm:py-8 lg:py-10'} pb-16 relative z-10 animate-fade-in text-slate-800`}>
      
      {/* Header & Sub-tab Switcher - An di khi thu nho sidebar de uu tien theo doi bang nhan vien */}
      {!isCollapsed && (
        <>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h1 className="text-[24px] sm:text-[28px] font-bold text-slate-900 tracking-tight">Quản lý nhân sự</h1>
              <p className="text-[13px] text-slate-500 mt-0.5">
                Quản lý hồ sơ nhân viên và lịch trực ca làm việc đồng bộ SharePoint
              </p>
            </div>

            {activeTab === 'employees' ? (
              <button 
                onClick={() => setIsAddModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-[12px] font-bold text-[14px] transition-colors shadow-sm cursor-pointer self-start sm:self-auto"
              >
                <Plus className="w-4 h-4" />
                Thêm nhân viên
              </button>
            ) : (
              <div className="flex items-center gap-2 self-start sm:self-auto">
                <button
                  onClick={() => setIsAuthModalOpen(true)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-[13px] font-bold transition-all border shadow-xs cursor-pointer ${
                    authStatus.authenticated
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100/70'
                      : 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100/70'
                  }`}
                  title="Quản lý phiên đăng nhập và Cookie Mail công ty"
                >
                  <KeyRound className="w-4 h-4" />
                  {authStatus.authenticated ? 'Mail công ty: Đã kết nối' : 'Đăng nhập Mail công ty'}
                </button>
                
                <button
                  onClick={() => {
                    setLinkFormData({
                      month: selectedMonth,
                      sharepointUrl: scheduleLink?.sharepointUrl || '',
                      title: scheduleLink?.title || `Lịch làm việc Tháng ${selectedMonth.split('-')[1]}/${selectedMonth.split('-')[0]}`,
                      note: scheduleLink?.note || ''
                    });
                    setIsLinkModalOpen(true);
                  }}
                  className="flex items-center gap-2 px-3.5 py-2 bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 rounded-xl text-[13px] font-bold transition-colors shadow-xs cursor-pointer"
                >
                  <Edit2 className="w-4 h-4 text-slate-500" />
                  Cập nhật link tháng
                </button>
              </div>
            )}
          </div>

          {/* Modern Sub-tabs Navigation */}
          <div className="flex border-b border-slate-200/80 mb-6 gap-2">
            <button
              onClick={() => setActiveTab('employees')}
              className={`flex items-center gap-2.5 pb-3 px-4 font-bold text-[14px] border-b-2 transition-all cursor-pointer ${
                activeTab === 'employees'
                  ? 'border-emerald-600 text-emerald-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Users className="w-4 h-4" />
              Hồ sơ nhân sự
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
                {employees.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('schedule')}
              className={`flex items-center gap-2.5 pb-3 px-4 font-bold text-[14px] border-b-2 transition-all cursor-pointer ${
                activeTab === 'schedule'
                  ? 'border-emerald-600 text-emerald-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <Calendar className="w-4 h-4" />
              Lịch làm việc & Ca trực
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/80 font-bold uppercase tracking-wider">
                SharePoint
              </span>
            </button>
          </div>
        </>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* TAB 1: DANH SÁCH NHÂN SỰ                                                */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'employees' && (
        <>
          {/* Metrics (Combined Bento Grid - Compact) - An khi thu nho sidebar */}
          {!isCollapsed && (
            <div className="w-full max-w-[580px]">
              <GlassCard className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 sm:p-5 relative overflow-hidden mb-6 bg-white/60 shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-slate-200/60 rounded-2xl">
                <div className="relative z-10 pl-2">
                  <div className="mb-2">
                    <span className="text-[12px] font-bold text-slate-400 uppercase tracking-wider">Tổng nhân sự</span>
                  </div>
                  <div className="text-[44px] sm:text-[54px] font-black text-slate-800 leading-none tracking-tight">{metrics.total}</div>
                </div>

                <div className="relative z-10 w-full sm:w-[240px] flex flex-col gap-2">
                  <div className="bg-white/80 backdrop-blur-md border border-slate-200/60 px-3.5 py-2 rounded-xl flex justify-between items-center shadow-2xs">
                    <span className="text-[11.5px] font-bold text-slate-500 uppercase tracking-wider">FPT Shop</span>
                    <span className="text-[16px] font-bold text-slate-800 leading-none">{metrics.fpt}</span>
                  </div>

                  <div className="bg-white/80 backdrop-blur-md border border-slate-200/60 px-3.5 py-2 rounded-xl flex justify-between items-center shadow-2xs">
                    <span className="text-[11.5px] font-bold text-slate-500 uppercase tracking-wider">Long Châu</span>
                    <span className="text-[16px] font-bold text-slate-800 leading-none">{metrics.longchau}</span>
                  </div>

                  <div className="bg-white/80 backdrop-blur-md border border-slate-200/60 px-3.5 py-2 rounded-xl flex justify-between items-center shadow-2xs">
                    <span className="text-[11.5px] font-bold text-slate-500 uppercase tracking-wider">Vaccine</span>
                    <span className="text-[16px] font-bold text-slate-800 leading-none">{metrics.vaccine}</span>
                  </div>
                </div>
              </GlassCard>
            </div>
          )}

          {/* Filters & Compact Header Controls */}
          <div className="flex gap-2.5 sm:gap-3.5 mb-4 sm:mb-6 items-center flex-wrap">
            {/* Khi thu nho sidebar: hien thi subtab gon gang ngay tren thanh tim kiem */}
            {isCollapsed && (
              <div className="flex items-center bg-slate-100/90 rounded-xl p-1 border border-slate-200/60 shadow-2xs shrink-0">
                <button
                  type="button"
                  onClick={() => setActiveTab('employees')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-bold transition-all cursor-pointer bg-white text-emerald-700 shadow-2xs"
                >
                  <Users className="w-3.5 h-3.5" />
                  Hồ sơ ({employees.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('schedule')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-bold transition-all cursor-pointer text-slate-500 hover:text-slate-800"
                >
                  <Calendar className="w-3.5 h-3.5" />
                  Lịch trực
                </button>
              </div>
            )}

            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input 
                type="text" 
                placeholder="Tìm theo Mã Inside, Mail, họ tên..." 
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-[12px] border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-[14px]"
              />
            </div>
            
            <select 
              value={chainFilter}
              onChange={e => setChainFilter(e.target.value as any)}
              className="px-3.5 py-2 rounded-[12px] border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-[13.5px] font-medium"
            >
              <option value="All">Tất cả chuỗi</option>
              <option value="FPT Shop">FPT Shop</option>
              <option value="Long Châu">Long Châu</option>
              <option value="Vaccine">Vaccine</option>
            </select>
            
            <select 
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              className={`px-3.5 py-2 rounded-[12px] border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-[13.5px] font-medium ${isCollapsed ? '' : 'ml-auto'}`}
            >
              <option value="insideCode">Sắp xếp theo Mã Inside</option>
              <option value="id">Sắp xếp theo Mail</option>
              <option value="name">Sắp xếp theo Tên</option>
              <option value="chain">Sắp xếp theo Chuỗi</option>
              <option value="startDate">Sắp xếp theo Ngày bắt đầu</option>
            </select>

            {/* Khi thu nho sidebar: bo sung nut "+ Them nhan vien" ngay tai hang tim kiem */}
            {isCollapsed && (
              <button 
                type="button"
                onClick={() => setIsAddModalOpen(true)}
                className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-[12px] font-bold text-[13px] transition-colors shadow-sm cursor-pointer ml-auto shrink-0"
                title="Thêm nhân viên mới"
              >
                <Plus className="w-4 h-4" />
                <span className="hidden sm:inline">Thêm nhân viên</span>
              </button>
            )}
          </div>

          {/* Table */}
          <GlassCard className="overflow-hidden bg-white/80">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/50">
                    <th className="px-6 py-4 text-[13px] font-bold text-slate-500 uppercase tracking-wider">Mã Inside</th>
                    <th className="px-6 py-4 text-[13px] font-bold text-slate-500 uppercase tracking-wider">Mail</th>
                    <th className="px-6 py-4 text-[13px] font-bold text-slate-500 uppercase tracking-wider">Họ và tên</th>
                    <th className="px-6 py-4 text-[13px] font-bold text-slate-500 uppercase tracking-wider">Chuỗi</th>
                    <th className="px-6 py-4 text-[13px] font-bold text-slate-500 uppercase tracking-wider">Thâm niên</th>
                    <th className="px-6 py-4 text-[13px] font-bold text-slate-500 uppercase tracking-wider text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-slate-500 font-medium">Đang tải danh sách nhân viên...</td>
                    </tr>
                  ) : filteredEmployees.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-slate-500 font-medium">Không tìm thấy nhân viên phù hợp</td>
                    </tr>
                  ) : (
                    filteredEmployees.map((emp) => (
                      <tr key={emp.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 text-[14px] font-extrabold text-indigo-600 font-mono tracking-wide">
                          {emp.insideCode || '-'}
                        </td>
                        <td className="px-6 py-4 text-[14px] font-bold text-slate-900">{emp.id}</td>
                        <td className="px-6 py-4 text-[14px] font-medium text-slate-800">{emp.name}</td>
                        <td className="px-6 py-4 text-[14px] font-medium">
                          <span className={`px-2.5 py-1 rounded-full text-[12px] font-bold ${
                            emp.chain === 'FPT Shop' ? 'bg-orange-100 text-orange-700' :
                            emp.chain === 'Long Châu' ? 'bg-blue-100 text-blue-700' :
                            'bg-purple-100 text-purple-700'
                          }`}>
                            {emp.chain}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-[14px] font-medium text-slate-600">
                          {emp.startDate ? Math.max(0, Math.floor((Date.now() - new Date(emp.startDate).getTime()) / (1000 * 60 * 60 * 24 * 30.44))) + ' tháng' : '-'}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => { 
                                setSelectedEmployee(emp); 
                                setFormData({
                                  ...formData, 
                                  insideCode: emp.insideCode || '',
                                  name: emp.name, 
                                  position: emp.position || '', 
                                  status: emp.status, 
                                  startDate: emp.startDate || ''
                                }); 
                                setIsEditModalOpen(true); 
                              }}
                              className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                              title="Chỉnh sửa"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            {emp.status === 'Active' && (
                              <button
                                onClick={() => {
                                  setSelectedEmployee(emp);
                                  setMoveTarget(CHAINS.find(c => c !== emp.chain) || 'FPT Shop');
                                  setIsMoveModalOpen(true);
                                }}
                                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                                title="Chuyển chuỗi"
                              >
                                <MoveRight className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* TAB 2: LỊCH LÀM VIỆC & CA TRỰC (SHAREPOINT HUB)                          */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'schedule' && (
        <div className="space-y-6">
          
          {/* Month Selector & Controls Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white/70 backdrop-blur-md border border-slate-200/80 p-4 rounded-2xl shadow-xs">
            
            {/* Month Navigator */}
            <div className="flex items-center gap-3 flex-wrap">
              {/* Khi thu nho sidebar tren tab Lich truc: hien thi subtab switcher */}
              {isCollapsed && (
                <div className="flex items-center bg-slate-100/90 rounded-xl p-1 border border-slate-200/60 shadow-2xs shrink-0 mr-2">
                  <button
                    type="button"
                    onClick={() => setActiveTab('employees')}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-bold transition-all cursor-pointer text-slate-500 hover:text-slate-800"
                  >
                    <Users className="w-3.5 h-3.5" />
                    Hồ sơ ({employees.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('schedule')}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-bold transition-all cursor-pointer bg-white text-emerald-700 shadow-2xs"
                  >
                    <Calendar className="w-3.5 h-3.5" />
                    Lịch trực
                  </button>
                </div>
              )}
              <span className="text-[12px] font-bold text-slate-400 uppercase tracking-wider">Thời gian:</span>
              <div className="flex items-center bg-slate-100/90 rounded-xl p-1 border border-slate-200/60 shadow-2xs">
                <button
                  onClick={() => handleMonthChange(-1)}
                  className="p-1.5 hover:bg-white text-slate-600 hover:text-slate-900 rounded-lg transition-all cursor-pointer"
                  title="Tháng trước"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <div className="px-4 text-[14px] font-extrabold text-slate-800 select-none min-w-[140px] text-center">
                  {formatMonthTitle(selectedMonth)}
                </div>
                <button
                  onClick={() => handleMonthChange(1)}
                  className="p-1.5 hover:bg-white text-slate-600 hover:text-slate-900 rounded-lg transition-all cursor-pointer"
                  title="Tháng sau"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {selectedMonth === '2026-11' && (
                <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">
                  Hiện tại
                </span>
              )}
            </div>

            {/* Quick Actions Right */}
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={() => setIsUploadModalOpen(true)}
                className="flex items-center gap-2 px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100/80 text-indigo-700 border border-indigo-200/80 rounded-xl text-[13px] font-bold transition-all shadow-xs cursor-pointer"
                title="Tải lên file Excel ca trực tháng này"
              >
                <Upload className="w-4 h-4" />
                Import Excel ca trực
              </button>

              <button
                onClick={() => loadScheduleData(selectedMonth)}
                className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-all border border-slate-200 bg-white shadow-2xs cursor-pointer"
                title="Tải lại dữ liệu"
              >
                <RefreshCw className={`w-4 h-4 ${scheduleLoading ? 'animate-spin text-emerald-600' : ''}`} />
              </button>
            </div>
          </div>

          {/* SharePoint Hero Card */}
          <GlassCard className="p-5 sm:p-6 bg-gradient-to-br from-white/90 via-white/80 to-slate-50/70 border border-slate-200/80 shadow-sm relative overflow-hidden">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
              
              {/* Left Info */}
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-600/10 border border-emerald-500/20 flex items-center justify-center shrink-0 text-emerald-600">
                  <FileSpreadsheet className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="text-[17px] font-bold text-slate-900">
                      {scheduleLink?.title || `Bảng sắp ca SharePoint Tháng ${selectedMonth.split('-')[1]}/${selectedMonth.split('-')[0]}`}
                    </h2>
                    {scheduleLink?.fileName && (
                      <span className="px-2.5 py-0.5 rounded-lg bg-emerald-100/80 text-emerald-800 text-[11px] font-bold border border-emerald-200">
                        {scheduleLink.fileName}
                      </span>
                    )}
                  </div>

                  <p className="text-[13px] text-slate-500 mt-1 max-w-xl">
                    {scheduleLink?.note || 'Bảng tính phân công ca trực FPT Shop, Long Châu và Vaccine. Quản lý trực tiếp trên Excel Online SharePoint.'}
                  </p>

                  <div className="flex items-center gap-3 mt-3">
                    <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-slate-500">
                      <span className={`w-2 h-2 rounded-full ${authStatus.authenticated ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                      {authStatus.authenticated ? 'Session Mail công ty đang hoạt động' : 'Chưa lưu phiên Mail (Khuyến nghị đăng nhập)'}
                    </span>
                    <span className="text-slate-300">•</span>
                    <button
                      onClick={handleCopyLink}
                      className="inline-flex items-center gap-1 text-[12px] font-bold text-slate-600 hover:text-emerald-700 transition-colors cursor-pointer"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      {copied ? 'Đã sao chép link' : 'Sao chép link'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Action Buttons */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 shrink-0">
                <button
                  onClick={handleOpenSharePointTab}
                  className="flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-[14px] transition-all shadow-sm cursor-pointer"
                  title="Mở trực tiếp trên tab mới với quyền Mail công ty"
                >
                  <ExternalLink className="w-4 h-4" />
                  Mở bảng ca trực SharePoint
                </button>

                <button
                  onClick={handleOpenParallelWindow}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl font-bold text-[13px] transition-all shadow-2xs cursor-pointer"
                  title="Mở cửa sổ làm việc song song kích thước 1200x800"
                >
                  <AppWindow className="w-4 h-4 text-slate-500" />
                  Mở song song
                </button>
              </div>
            </div>
          </GlassCard>

          {/* Shift Matrix Section Header & Filters */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-8">
            <div>
              <h3 className="text-[17px] font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <span>Ma trận Ca làm việc nhân viên</span>
                <span className="text-[12px] font-medium text-slate-500">
                  ({filteredMatrixEmployees.length} nhân sự)
                </span>
              </h3>
              <p className="text-[12px] text-slate-500 mt-0.5">
                Màu sắc và trạng thái phân bổ đồng bộ trực tiếp từ file Excel SharePoint
              </p>
            </div>

            {/* Filter & Legend */}
            <div className="flex items-center gap-3 flex-wrap">
              <div className="relative min-w-[200px]">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Lọc tên, mã mail..."
                  value={matrixSearch}
                  onChange={e => setMatrixSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-800 placeholder:text-slate-400 text-[13px] outline-none focus:ring-2 focus:ring-emerald-500/50"
                />
              </div>

              <select
                value={matrixChainFilter}
                onChange={e => setMatrixChainFilter(e.target.value as any)}
                className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-800 text-[13px] font-semibold outline-none focus:ring-2 focus:ring-emerald-500/50"
              >
                <option value="All">Tất cả chuỗi</option>
                <option value="FPT Shop">FPT Shop</option>
                <option value="Long Châu">Long Châu</option>
                <option value="Vaccine">Vaccine</option>
              </select>
            </div>
          </div>

          {/* Shift Color Legend & Fast Navigation Controls */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 p-3.5 bg-white/70 border border-slate-200/80 rounded-2xl shadow-2xs">
            {/* Shift Color Legend */}
            <div className="flex items-center gap-2 flex-wrap text-[11.5px]">
              <span className="font-bold text-slate-400 uppercase tracking-wider mr-1">Chú thích:</span>
              <span className="px-2 py-0.5 rounded-md bg-sky-100 text-sky-800 border border-sky-200 font-semibold">Ca Sáng</span>
              <span className="px-2 py-0.5 rounded-md bg-teal-100 text-teal-800 border border-teal-200 font-semibold">Ca Chiều</span>
              <span className="px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 border border-amber-300 font-bold">Trực đêm</span>
              <span className="px-2 py-0.5 rounded-md bg-indigo-100 text-indigo-800 border border-indigo-300 font-bold">Sáng + đêm</span>
              <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200 font-medium">OFF</span>
              <span className="px-2 py-0.5 rounded-md bg-slate-200 text-slate-700 border border-slate-300 font-medium">OFF BÙ</span>
              <span className="px-2 py-0.5 rounded-md bg-rose-100 text-rose-700 border border-rose-200 font-semibold">OFF PHÉP</span>
            </div>

            {/* Week Range Filter & Quick Scroll Buttons */}
            <div className="flex items-center gap-2 flex-wrap self-end lg:self-auto">
              <div className="flex items-center bg-slate-100/90 p-0.5 rounded-xl border border-slate-200/80 text-[12px] font-bold">
                <button
                  onClick={() => setDateRangeFilter('all')}
                  className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                    dateRangeFilter === 'all' ? 'bg-white text-emerald-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Cả tháng ({matrixData?.dates.length || 30} ngày)
                </button>
                <button
                  onClick={() => setDateRangeFilter('w1')}
                  className={`px-2 py-1 rounded-lg transition-all cursor-pointer ${
                    dateRangeFilter === 'w1' ? 'bg-white text-emerald-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  T1 (01-07)
                </button>
                <button
                  onClick={() => setDateRangeFilter('w2')}
                  className={`px-2 py-1 rounded-lg transition-all cursor-pointer ${
                    dateRangeFilter === 'w2' ? 'bg-white text-emerald-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  T2 (08-14)
                </button>
                <button
                  onClick={() => setDateRangeFilter('w3')}
                  className={`px-2 py-1 rounded-lg transition-all cursor-pointer ${
                    dateRangeFilter === 'w3' ? 'bg-white text-emerald-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  T3 (15-21)
                </button>
                <button
                  onClick={() => setDateRangeFilter('w4')}
                  className={`px-2 py-1 rounded-lg transition-all cursor-pointer ${
                    dateRangeFilter === 'w4' ? 'bg-white text-emerald-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  T4 (22-30)
                </button>
              </div>

              {/* Scroll controls */}
              <div className="flex items-center gap-1">
                <button
                  onClick={() => scrollTable('left')}
                  className="px-2 py-1 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-lg text-[12px] font-bold shadow-2xs transition-colors cursor-pointer"
                  title="Cuộn sang trái"
                >
                  ◀
                </button>
                <button
                  onClick={() => scrollTable('start')}
                  className="px-2 py-1 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-lg text-[11px] font-bold shadow-2xs transition-colors cursor-pointer"
                  title="Đầu tháng"
                >
                  Đầu
                </button>
                <button
                  onClick={() => scrollTable('end')}
                  className="px-2 py-1 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-lg text-[11px] font-bold shadow-2xs transition-colors cursor-pointer"
                  title="Cuối tháng"
                >
                  Cuối
                </button>
                <button
                  onClick={() => scrollTable('right')}
                  className="px-2 py-1 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-lg text-[12px] font-bold shadow-2xs transition-colors cursor-pointer"
                  title="Cuộn sang phải"
                >
                  ▶
                </button>
              </div>
            </div>
          </div>

          {/* Shift Matrix Table */}
          <GlassCard className="overflow-hidden bg-white/95 border border-slate-200/80 shadow-xs">
            <div 
              ref={tableContainerRef}
              className="overflow-x-auto max-h-[620px] relative scroll-smooth"
            >
              <table className="w-full text-left border-collapse text-[13px]">
                <thead className="sticky top-0 z-30 bg-slate-100 shadow-2xs border-b border-slate-200">
                  <tr>
                    {/* Fixed Headers with solid opaque background */}
                    <th className="px-3.5 py-3 font-bold text-slate-700 uppercase tracking-wider sticky left-0 z-40 bg-slate-100 min-w-[75px] max-w-[85px] border-r border-slate-200 shadow-[2px_0_4px_rgba(0,0,0,0.03)] text-[12px]">
                      Mã NV
                    </th>
                    <th className="px-3.5 py-3 font-bold text-slate-700 uppercase tracking-wider sticky left-[75px] z-40 bg-slate-100 min-w-[100px] max-w-[110px] border-r border-slate-200 shadow-[2px_0_4px_rgba(0,0,0,0.03)] text-[12px]">
                      Mail
                    </th>
                    <th className="px-3.5 py-3 font-bold text-slate-700 uppercase tracking-wider sticky left-[175px] z-40 bg-slate-100 min-w-[155px] max-w-[170px] border-r border-slate-200 shadow-[4px_0_6px_rgba(0,0,0,0.05)] text-[12px]">
                      Họ và tên
                    </th>

                    {/* Date Column Headers */}
                    {(matrixData?.dates || [])
                      .filter((dh) => {
                        if (dateRangeFilter === 'all') return true;
                        const day = parseInt(dh.date.slice(8), 10);
                        if (dateRangeFilter === 'w1') return day >= 1 && day <= 7;
                        if (dateRangeFilter === 'w2') return day >= 8 && day <= 14;
                        if (dateRangeFilter === 'w3') return day >= 15 && day <= 21;
                        if (dateRangeFilter === 'w4') return day >= 22;
                        return true;
                      })
                      .map((dh, idx) => {
                        const isSunday = dh.dayOfWeek?.toLowerCase().includes('chủ') || dh.dayOfWeek?.toLowerCase().includes('cn');
                        return (
                          <th 
                            key={dh.date + idx} 
                            className={`px-1.5 py-2.5 text-center min-w-[70px] sm:min-w-[78px] border-r border-slate-200 select-none ${
                              isSunday ? 'bg-rose-50 text-rose-900 font-black' : 'text-slate-700 font-bold'
                            }`}
                          >
                            <div className="text-[10.5px] font-bold text-slate-500 uppercase">{dh.dayOfWeek}</div>
                            <div className="text-[12px] font-black">{dh.date.slice(5).replace('-', '/')}</div>
                          </th>
                        );
                      })}
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {scheduleLoading ? (
                    <tr>
                      <td colSpan={35} className="px-6 py-12 text-center text-slate-500 font-medium">
                        <RefreshCw className="w-5 h-5 animate-spin mx-auto text-emerald-600 mb-2" />
                        Đang nạp bảng ma trận ca trực...
                      </td>
                    </tr>
                  ) : filteredMatrixEmployees.length === 0 ? (
                    <tr>
                      <td colSpan={35} className="px-6 py-12 text-center text-slate-500 font-medium">
                        Không có dữ liệu ca trực cho bộ lọc này. Bạn có thể bấm "Import Excel ca trực" để nạp file của tháng.
                      </td>
                    </tr>
                  ) : (
                    filteredMatrixEmployees.map((emp) => (
                      <tr key={emp.id} className="hover:bg-slate-50/80 transition-colors">
                        {/* Sticky Code */}
                        <td className="px-3.5 py-2.5 font-bold text-slate-800 sticky left-0 z-20 bg-white border-r border-slate-100 shadow-[2px_0_4px_rgba(0,0,0,0.03)] text-[12px]">
                          {emp.code || '-'}
                        </td>
                        {/* Sticky Mail */}
                        <td className="px-3.5 py-2.5 font-bold text-slate-900 sticky left-[75px] z-20 bg-white border-r border-slate-100 shadow-[2px_0_4px_rgba(0,0,0,0.03)] text-[13px]">
                          {emp.id}
                        </td>
                        {/* Sticky Name */}
                        <td className="px-3.5 py-2.5 font-medium text-slate-800 sticky left-[175px] z-20 bg-white border-r border-slate-100 whitespace-nowrap shadow-[4px_0_6px_rgba(0,0,0,0.05)] text-[13px]">
                          {emp.name}
                        </td>

                        {/* Shifts for each date */}
                        {(matrixData?.dates || [])
                          .filter((dh) => {
                            if (dateRangeFilter === 'all') return true;
                            const day = parseInt(dh.date.slice(8), 10);
                            if (dateRangeFilter === 'w1') return day >= 1 && day <= 7;
                            if (dateRangeFilter === 'w2') return day >= 8 && day <= 14;
                            if (dateRangeFilter === 'w3') return day >= 15 && day <= 21;
                            if (dateRangeFilter === 'w4') return day >= 22;
                            return true;
                          })
                          .map((dh, idx) => {
                            const shift = emp.shifts[dh.date] || '';
                            return (
                              <td key={dh.date + idx} className="px-1 py-2 text-center border-r border-slate-100">
                                {shift ? (
                                  <span className={`inline-block px-1.5 py-1 rounded text-[11px] whitespace-nowrap ${getShiftBadgeClass(shift)}`}>
                                    {shift}
                                  </span>
                                ) : (
                                  <span className="text-slate-300">-</span>
                                )}
                              </td>
                            );
                          })}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* MODALS                                                                  */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}

      {/* 1. Modal Cập nhật Link SharePoint theo Tháng */}
      {isLinkModalOpen && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-[24px] p-6 sm:p-8 w-full max-w-lg shadow-2xl">
            <div className="flex justify-between items-center mb-5">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Cấu hình Link SharePoint</h2>
                <p className="text-[13px] text-slate-500">Lưu đường dẫn ca trực cho từng tháng vào hệ thống</p>
              </div>
              <button onClick={() => setIsLinkModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5"/>
              </button>
            </div>

            {linkFormError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-100 text-rose-600 rounded-xl text-sm flex gap-2 items-center">
                <ShieldAlert className="w-4 h-4 shrink-0" /> {linkFormError}
              </div>
            )}

            <form onSubmit={handleSaveLink} className="space-y-4">
              <div>
                <label className="block text-[13px] font-bold text-slate-700 mb-1">Tháng áp dụng (YYYY-MM) *</label>
                <input 
                  required 
                  type="month" 
                  value={linkFormData.month} 
                  onChange={e => setLinkFormData({...linkFormData, month: e.target.value})} 
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 font-semibold focus:ring-2 focus:ring-emerald-500/50 outline-none"
                />
              </div>

              <div>
                <label className="block text-[13px] font-bold text-slate-700 mb-1">Tiêu đề hiển thị</label>
                <input 
                  type="text" 
                  placeholder="Ví dụ: Lịch làm việc Tháng 11/2026"
                  value={linkFormData.title} 
                  onChange={e => setLinkFormData({...linkFormData, title: e.target.value})} 
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none"
                />
              </div>

              <div>
                <label className="block text-[13px] font-bold text-slate-700 mb-1">Đường dẫn SharePoint (.xlsx) *</label>
                <textarea 
                  required 
                  rows={3}
                  placeholder="https://fptsoftware362.sharepoint.com/:x:/r/sites/..."
                  value={linkFormData.sharepointUrl} 
                  onChange={e => setLinkFormData({...linkFormData, sharepointUrl: e.target.value})} 
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none text-[13px] font-mono"
                />
                <span className="text-[11px] text-slate-400 block mt-1">
                  Hệ thống sẽ tự trích xuất tên file (ví dụ: 1. LLV T11 2026.xlsx) từ tham số của đường link.
                </span>
              </div>

              <div>
                <label className="block text-[13px] font-bold text-slate-700 mb-1">Ghi chú (Tùy chọn)</label>
                <input 
                  type="text" 
                  placeholder="Ghi chú phân công hoặc người phụ trách..."
                  value={linkFormData.note} 
                  onChange={e => setLinkFormData({...linkFormData, note: e.target.value})} 
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none text-[13px]"
                />
              </div>

              <div className="flex gap-3 justify-end mt-8">
                <button 
                  type="button" 
                  onClick={() => setIsLinkModalOpen(false)} 
                  className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  Hủy
                </button>
                <button 
                  type="submit" 
                  className="px-5 py-2.5 rounded-xl font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-sm cursor-pointer"
                >
                  Lưu liên kết tháng
                </button>
              </div>
            </form>
          </div>
        </div>,
        document.body
      )}

      {/* 2. Modal Đăng nhập Mail công ty & Quản lý Session Cookie */}
      {isAuthModalOpen && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-[24px] p-6 sm:p-8 w-full max-w-lg shadow-2xl">
            <div className="flex justify-between items-center mb-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Quản lý Mail & Session Cookie</h2>
                  <p className="text-[12px] text-slate-500">Xác thực Microsoft 365 / SharePoint</p>
                </div>
              </div>
              <button onClick={() => setIsAuthModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5"/>
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-4 rounded-xl border bg-slate-50/70 border-slate-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[13px] font-bold text-slate-700">Trạng thái xác thực:</span>
                  <span className={`px-2.5 py-1 rounded-full text-[12px] font-bold ${
                    authStatus.authenticated 
                      ? 'bg-emerald-100 text-emerald-800' 
                      : 'bg-amber-100 text-amber-800'
                  }`}>
                    {authStatus.authenticated ? 'ĐÃ KẾT NỐI' : 'CHƯA LƯU PHIÊN'}
                  </span>
                </div>
                <p className="text-[12px] text-slate-500 leading-relaxed">
                  {authStatus.authenticated 
                    ? 'Session cookie của Mail công ty đã được lưu trữ vĩnh viễn trên Chrome profile độc lập. Bạn có thể mở bảng ca trực trực tiếp bất cứ lúc nào.'
                    : 'Hệ thống cần bạn đăng nhập Mail công ty một lần để lưu trữ cookie phiên làm việc. Nhấn nút bên dưới để mở trình duyệt đăng nhập Microsoft.'}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-100 text-[12.5px] text-blue-900 leading-relaxed">
                <strong>🔒 Lưu ý bảo mật:</strong>
                <ul className="list-disc list-inside mt-1.5 space-y-1 text-[12px] text-blue-800">
                  <li>Session cookie được lưu an toàn trong máy nội bộ của bạn.</li>
                  <li>Không bao giờ bị commit hoặc đẩy lên kho lưu trữ GitHub công khai.</li>
                  <li>Khi đổi mật khẩu hoặc hết hạn phiên, chỉ cần bấm đăng nhập lại.</li>
                </ul>
              </div>

              <div className="flex gap-3 justify-end mt-6">
                {authStatus.authenticated ? (
                  <>
                    <button
                      type="button"
                      onClick={handleLogoutAuthSession}
                      className="px-4 py-2.5 rounded-xl font-bold text-rose-600 hover:bg-rose-50 border border-rose-200 transition-colors text-[13px] cursor-pointer flex items-center gap-2"
                    >
                      <LogOut className="w-4 h-4" />
                      Đăng xuất & Xóa cookie
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsAuthModalOpen(false)}
                      className="px-5 py-2.5 rounded-xl font-bold text-white bg-slate-800 hover:bg-slate-900 transition-colors shadow-sm cursor-pointer"
                    >
                      Đóng
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => setIsAuthModalOpen(false)}
                      className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
                    >
                      Để sau
                    </button>
                    <button
                      type="button"
                      onClick={handleStartAuthSession}
                      className="px-5 py-2.5 rounded-xl font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-sm cursor-pointer flex items-center gap-2"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Mở cửa sổ Đăng nhập Microsoft
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* 3. Modal Import File Excel Ca trực */}
      {isUploadModalOpen && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-[24px] p-6 sm:p-8 w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-5">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Import Excel Ca trực</h2>
                <p className="text-[12px] text-slate-500">Tải lên file .xlsx xuất từ SharePoint ({formatMonthTitle(selectedMonth)})</p>
              </div>
              <button onClick={() => setIsUploadModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5"/>
              </button>
            </div>

            {uploadSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-100 text-emerald-700 rounded-xl text-[13px] flex gap-2 items-center font-bold">
                <Check className="w-4 h-4" /> {uploadSuccess}
              </div>
            )}

            <form onSubmit={handleImportExcelSubmit} className="space-y-4">
              <div className="border-2 border-dashed border-slate-200 hover:border-emerald-500/70 rounded-2xl p-6 text-center transition-all bg-slate-50/50">
                <FileSpreadsheet className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                <label className="block text-[13px] font-bold text-slate-700 mb-1 cursor-pointer">
                  Chọn file <span className="text-emerald-600 underline">1. LLV.xlsx</span>
                </label>
                <input
                  type="file"
                  accept=".xlsx"
                  onChange={e => setUploadFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="excel-file-input"
                />
                <label
                  htmlFor="excel-file-input"
                  className="inline-block mt-2 px-4 py-1.5 bg-white border border-slate-200 text-slate-700 rounded-xl text-[12px] font-bold hover:bg-slate-100 transition-colors cursor-pointer shadow-2xs"
                >
                  Duyệt file trên máy
                </label>

                {uploadFile && (
                  <div className="mt-3 text-[12px] font-bold text-emerald-700 bg-emerald-50 py-1.5 px-3 rounded-lg border border-emerald-200 inline-block">
                    {uploadFile.name} ({(uploadFile.size / 1024).toFixed(1)} KB)
                  </div>
                )}
              </div>

              <p className="text-[12px] text-slate-400 leading-relaxed">
                * Hệ thống sẽ đọc dữ liệu từ sheet <strong>LLV</strong> và cập nhật ca trực cho toàn bộ nhân sự theo ngày.
              </p>

              <div className="flex gap-3 justify-end mt-6">
                <button
                  type="button"
                  onClick={() => setIsUploadModalOpen(false)}
                  className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={!uploadFile || isUploading}
                  className="px-5 py-2.5 rounded-xl font-bold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 transition-colors shadow-sm cursor-pointer flex items-center gap-2"
                >
                  {isUploading && <RefreshCw className="w-4 h-4 animate-spin" />}
                  {isUploading ? 'Đang nạp dữ liệu...' : 'Xác nhận nạp'}
                </button>
              </div>
            </form>
          </div>
        </div>,
        document.body
      )}

      {/* Add Employee Modal */}
      {isAddModalOpen && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-[24px] p-8 w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-slate-900">Thêm nhân viên mới</h2>
              <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer"><X className="w-5 h-5"/></button>
            </div>
            
            {formError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-100 text-rose-600 rounded-lg text-sm flex gap-2 items-center">
                <ShieldAlert className="w-4 h-4" /> {formError}
              </div>
            )}

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[13px] font-bold text-slate-700 mb-1">Mã Inside</label>
                  <input type="text" placeholder="VD: 51765" value={formData.insideCode} onChange={e => setFormData({...formData, insideCode: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none font-mono"/>
                </div>
                <div>
                  <label className="block text-[13px] font-bold text-slate-700 mb-1">Mail *</label>
                  <input required type="text" placeholder="VD: VienND2" value={formData.id} onChange={e => setFormData({...formData, id: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none"/>
                </div>
              </div>
              <div>
                <label className="block text-[13px] font-bold text-slate-700 mb-1">Họ và tên *</label>
                <input required type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none"/>
              </div>
              <div>
                <label className="block text-[13px] font-bold text-slate-700 mb-1">Chuỗi *</label>
                <select required value={formData.chain} onChange={e => setFormData({...formData, chain: e.target.value as Chain})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500/50 outline-none">
                  {CHAINS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-[13px] font-bold text-slate-700 mb-1">Ngày bắt đầu</label>
                <input type="date" value={formData.startDate || ''} onChange={e => setFormData({...formData, startDate: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500/50 outline-none"/>
              </div>
              
              <div className="flex gap-3 justify-end mt-8">
                <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer">Hủy</button>
                <button type="submit" className="px-5 py-2.5 rounded-xl font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-sm cursor-pointer">Thêm nhân viên</button>
              </div>
            </form>
          </div>
        </div>,
        document.body
      )}

      {/* Edit Employee Modal */}
      {isEditModalOpen && selectedEmployee && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-[24px] p-8 w-full max-w-md shadow-2xl">
            <h2 className="text-xl font-bold text-slate-900 mb-6">Chỉnh sửa nhân viên</h2>
            {isDeleteConfirmOpen ? (
              <div className="space-y-6">
                <div className="p-4 bg-rose-50 rounded-xl border border-rose-100 flex items-start gap-3 text-rose-800">
                  <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-bold mb-1">Xóa vĩnh viễn nhân viên?</h3>
                    <p className="text-[13px] leading-relaxed">
                      Bạn sắp xóa nhân viên <strong>{selectedEmployee.name}</strong> ({selectedEmployee.id}). Hành động này không thể hoàn tác và sẽ xóa nhân viên khỏi hệ thống.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3 justify-end">
                  <button type="button" onClick={() => setIsDeleteConfirmOpen(false)} className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer">Quay lại</button>
                  <button 
                    type="button" 
                    onClick={() => {
                      setEmployees(prev => prev.filter(e => e.id !== selectedEmployee.id));
                      EmployeeService.deleteEmployee(selectedEmployee.id);
                      setIsDeleteConfirmOpen(false);
                      setIsEditModalOpen(false);
                      setSelectedEmployee(null);
                    }}
                    className="px-5 py-2.5 rounded-xl font-bold text-white bg-rose-600 hover:bg-rose-700 transition-colors shadow-sm cursor-pointer"
                  >
                    Xác nhận xóa
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleEditSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[13px] font-bold text-slate-700 mb-1">Mã Inside</label>
                    <input type="text" placeholder="VD: 51765" value={formData.insideCode} onChange={e => setFormData({...formData, insideCode: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none font-mono"/>
                  </div>
                  <div>
                    <label className="block text-[13px] font-bold text-slate-700 mb-1">Mail (Không thể đổi)</label>
                    <input disabled type="text" value={selectedEmployee.id} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-500 cursor-not-allowed outline-none"/>
                  </div>
                </div>
                <div>
                  <label className="block text-[13px] font-bold text-slate-700 mb-1">Họ và tên *</label>
                  <input required type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none"/>
                </div>
                <div>
                  <label className="block text-[13px] font-bold text-slate-700 mb-1">Ngày bắt đầu</label>
                  <input type="date" value={formData.startDate || ''} onChange={e => setFormData({...formData, startDate: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-emerald-500/50 outline-none"/>
                </div>
                <div className="flex gap-3 justify-between mt-8">
                  <button
                    type="button"
                    onClick={() => setIsDeleteConfirmOpen(true)}
                    className="px-4 py-2.5 rounded-xl font-bold text-rose-600 hover:bg-rose-50 border border-rose-200 transition-colors text-[13px] cursor-pointer"
                  >
                    Xóa nhân viên
                  </button>
                  <div className="flex gap-3">
                    <button type="button" onClick={() => setIsEditModalOpen(false)} className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer">Hủy</button>
                    <button type="submit" className="px-5 py-2.5 rounded-xl font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-sm cursor-pointer">Lưu thay đổi</button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>,
        document.body
      )}

      {/* Move Employee Modal */}
      {isMoveModalOpen && selectedEmployee && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-[24px] p-8 w-full max-w-md shadow-2xl">
            <h2 className="text-xl font-bold text-slate-900 mb-6">CHUYỂN CHUỖI</h2>
            
            <div className="space-y-4 mb-6">
              <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                <span className="text-slate-500 font-medium">Nhân viên:</span>
                <span className="font-bold text-slate-900">{selectedEmployee.name}</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                <span className="text-slate-500 font-medium">Mail:</span>
                <span className="font-bold text-slate-900">{selectedEmployee.id}</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                <span className="text-slate-500 font-medium">Chuỗi hiện tại:</span>
                <span className="font-bold text-slate-900">{selectedEmployee.chain}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-medium">Chuỗi mới:</span>
                <select 
                  value={moveTarget}
                  onChange={e => setMoveTarget(e.target.value as Chain)}
                  className="px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500/50 outline-none font-bold text-emerald-700 cursor-pointer"
                >
                  {CHAINS.filter(c => c !== selectedEmployee.chain).map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="p-4 bg-amber-50 rounded-xl border border-amber-100 mb-8">
              <p className="text-[13px] text-amber-800 font-medium leading-relaxed">
                Bạn có chắc muốn chuyển <strong>{selectedEmployee.name}</strong> từ {selectedEmployee.chain} sang {moveTarget}?
                <br/><br/>
                Sau khi chuyển, nhân viên sẽ xuất hiện trong danh sách quản lý của {moveTarget}.
              </p>
            </div>

            <div className="flex gap-3 justify-end">
              <button onClick={() => setIsMoveModalOpen(false)} className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer">Hủy</button>
              <button onClick={handleMoveSubmit} className="px-5 py-2.5 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm cursor-pointer">Xác nhận chuyển</button>
            </div>
          </div>
        </div>,
        document.body
      )}

    </div>
  );
};

export default Employees;
