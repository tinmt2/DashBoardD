import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Search, Plus, Edit2, MoveRight, ShieldAlert, X, Check, LayoutGrid, Columns, Table } from 'lucide-react';
import { EmployeeService } from '../services/employeeService';
import type { Employee, Chain } from '../types';
import { GlassCard } from '../components/common/GlassCard';

const CHAINS: Chain[] = ['FPT Shop', 'Long Châu', 'Vaccine'];

interface EmployeeNoteCellProps {
  employeeId: string;
  initialNote?: string;
  onSaved?: (newNote: string) => void;
}

const EmployeeNoteCell: React.FC<EmployeeNoteCellProps> = ({ employeeId, initialNote = '', onSaved }) => {
  const [note, setNote] = useState(initialNote || '');
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    setNote(initialNote || '');
  }, [initialNote]);

  const handleSave = async () => {
    const trimmed = note.trim();
    if (trimmed === (initialNote || '').trim()) return;
    setIsSaving(true);
    try {
      await EmployeeService.updateNote(employeeId, trimmed);
      setIsSaved(true);
      onSaved?.(trimmed);
      setTimeout(() => setIsSaved(false), 2000);
    } catch (e) {
      console.error("Lỗi khi lưu ghi chú nhân viên:", e);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="relative flex items-center w-full min-w-[100px]">
      <input
        type="text"
        value={note}
        onChange={e => {
          setNote(e.target.value);
          setIsSaved(false);
        }}
        onBlur={handleSave}
        onKeyDown={e => {
          if (e.key === 'Enter') {
            (e.target as HTMLInputElement).blur();
          }
        }}
        placeholder="Ghi chú..."
        title="Nhập ghi chú thay đổi (tự động lưu vĩnh viễn)"
        className={`w-full pl-2 pr-5 py-0.5 text-[11.5px] leading-tight rounded border transition-all outline-none text-slate-800 placeholder:text-slate-300 ${
          isSaved 
            ? 'border-emerald-400 bg-emerald-50/70 text-emerald-900 font-medium' 
            : 'border-slate-200/80 bg-white hover:border-slate-300 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 shadow-2xs'
        }`}
      />
      {isSaving && (
        <span className="absolute right-1 text-[9px] text-slate-400 font-semibold select-none animate-pulse">Lưu...</span>
      )}
      {isSaved && !isSaving && (
        <Check className="w-3 h-3 text-emerald-600 absolute right-1 pointer-events-none transition-opacity" />
      )}
    </div>
  );
};

interface CompactEmployeeTableProps {
  employees: Employee[];
  showChainColumn?: boolean;
  onEdit: (emp: Employee) => void;
  onMove: (emp: Employee) => void;
  onSaveNote: (id: string, note: string) => void;
  loading?: boolean;
  emptyText?: string;
}

const CompactEmployeeTable: React.FC<CompactEmployeeTableProps> = ({
  employees,
  showChainColumn = true,
  onEdit,
  onMove,
  onSaveNote,
  loading = false,
  emptyText = 'Không tìm thấy nhân viên'
}) => {
  const colSpanCount = showChainColumn ? 7 : 6;

  return (
    <div className="overflow-x-auto w-full">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-slate-200/80 bg-slate-50/80 text-[11px] font-bold text-slate-500 uppercase tracking-wider select-none">
            <th className="px-2.5 py-1.5 whitespace-nowrap">Mã</th>
            <th className="px-2 py-1.5 whitespace-nowrap">Mail</th>
            <th className="px-2 py-1.5 whitespace-nowrap">Họ và tên</th>
            {showChainColumn && <th className="px-2 py-1.5 whitespace-nowrap">Chuỗi</th>}
            <th className="px-1.5 py-1.5 whitespace-nowrap text-center">TN</th>
            <th className="px-2 py-1.5 min-w-[110px]">Thay đổi</th>
            <th className="px-2 py-1.5 text-right whitespace-nowrap">Thao tác</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-[12px]">
          {loading ? (
            <tr>
              <td colSpan={colSpanCount} className="px-4 py-6 text-center text-slate-400 font-medium">
                Đang tải danh sách...
              </td>
            </tr>
          ) : employees.length === 0 ? (
            <tr>
              <td colSpan={colSpanCount} className="px-4 py-6 text-center text-slate-400 font-medium">
                {emptyText}
              </td>
            </tr>
          ) : (
            employees.map((emp) => {
              const months = emp.startDate 
                ? Math.max(0, Math.floor((Date.now() - new Date(emp.startDate).getTime()) / (1000 * 60 * 60 * 24 * 30.44)))
                : null;

              return (
                <tr key={emp.id} className="hover:bg-blue-50/30 transition-colors h-[28px] sm:h-[30px]">
                  <td className="px-2.5 py-0.5 font-extrabold text-indigo-600 font-mono tracking-tight whitespace-nowrap">
                    {emp.insideCode || '-'}
                  </td>
                  <td className="px-2 py-0.5 font-bold text-slate-900 whitespace-nowrap">
                    {emp.id}
                  </td>
                  <td className="px-2 py-0.5 font-medium text-slate-800 truncate max-w-[125px]" title={emp.name}>
                    {emp.name}
                  </td>
                  {showChainColumn && (
                    <td className="px-2 py-0.5 whitespace-nowrap">
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                        emp.chain === 'FPT Shop' ? 'bg-orange-100 text-orange-700' :
                        emp.chain === 'Long Châu' ? 'bg-blue-100 text-blue-700' :
                        'bg-purple-100 text-purple-700'
                      }`}>
                        {emp.chain}
                      </span>
                    </td>
                  )}
                  <td className="px-1.5 py-0.5 text-center text-slate-500 whitespace-nowrap font-medium text-[11px]" title={`Bắt đầu: ${emp.startDate || 'Chưa có'}`}>
                    {months !== null ? `${months}th` : '-'}
                  </td>
                  <td className="px-2 py-0.5">
                    <EmployeeNoteCell
                      employeeId={emp.id}
                      initialNote={emp.note}
                      onSaved={(newNote) => onSaveNote(emp.id, newNote)}
                    />
                  </td>
                  <td className="px-2 py-0.5 text-right whitespace-nowrap">
                    <div className="flex justify-end gap-1 items-center">
                      <button
                        type="button"
                        onClick={() => onEdit(emp)}
                        className="p-1 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded transition-colors cursor-pointer"
                        title="Chỉnh sửa"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      {emp.status === 'Active' && (
                        <button
                          type="button"
                          onClick={() => onMove(emp)}
                          className="p-1 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors cursor-pointer"
                          title="Chuyển chuỗi"
                        >
                          <MoveRight className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};

const Employees: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  
  // View mode: 'by_chain' (3 columns, zero scroll), 'two_columns' (2 columns, zero scroll), 'single' (compact single table)
  const [viewMode, setViewMode] = useState<'by_chain' | 'two_columns' | 'single'>(() => {
    return (localStorage.getItem('employee_view_mode') as any) || 'by_chain';
  });

  const handleSetViewMode = (mode: 'by_chain' | 'two_columns' | 'single') => {
    setViewMode(mode);
    localStorage.setItem('employee_view_mode', mode);
  };

  // Filters
  const [search, setSearch] = useState('');
  const [chainFilter, setChainFilter] = useState<Chain | 'All'>('All');
  const [sortBy, setSortBy] = useState<'insideCode' | 'name' | 'id' | 'chain' | 'startDate'>('insideCode');
  
  // Modals
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isMoveModalOpen, setIsMoveModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  
  // Form State
  const [formData, setFormData] = useState({
    id: '',
    insideCode: '',
    name: '',
    chain: 'FPT Shop' as Chain,
    position: '',
    status: 'Active' as 'Active' | 'Inactive',
    startDate: '',
    note: ''
  });
  const [formError, setFormError] = useState('');
  const [moveTarget, setMoveTarget] = useState<Chain>('FPT Shop');

  useEffect(() => {
    loadEmployees();
  }, []);

  const loadEmployees = async () => {
    setLoading(true);
    try {
      const data = await EmployeeService.getEmployees();
      setEmployees(data);
    } catch (e) {
      console.error("Error loading employees:", e);
    } finally {
      setLoading(false);
    }
  };

  const updateLocalEmployee = (updated: Employee) => {
    setEmployees(prev => prev.map(e => e.id === updated.id ? updated : e));
  };

  const handleSaveNote = (empId: string, newNote: string) => {
    setEmployees(prev => prev.map(e => e.id === empId ? { ...e, note: newNote } : e));
  };

  const openEditModal = (emp: Employee) => {
    setSelectedEmployee(emp); 
    setFormData({
      id: emp.id,
      insideCode: emp.insideCode || '',
      name: emp.name, 
      chain: emp.chain,
      position: emp.position || '', 
      status: emp.status, 
      startDate: emp.startDate || '',
      note: emp.note || ''
    }); 
    setIsEditModalOpen(true);
  };

  const openMoveModal = (emp: Employee) => {
    setSelectedEmployee(emp);
    setMoveTarget(CHAINS.find(c => c !== emp.chain) || 'FPT Shop');
    setIsMoveModalOpen(true);
  };

  const filteredEmployees = employees.filter(emp => {
    if (chainFilter !== 'All' && emp.chain !== chainFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      const matchName = emp.name.toLowerCase().includes(q);
      const matchId = emp.id.toLowerCase().includes(q);
      const matchInside = (emp.insideCode || '').toLowerCase().includes(q);
      const matchNote = (emp.note || '').toLowerCase().includes(q);
      if (!matchName && !matchId && !matchInside && !matchNote) return false;
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

  // Groups for 3-Column By-Chain mode
  const fptEmps = filteredEmployees.filter(e => e.chain === 'FPT Shop');
  const longchauEmps = filteredEmployees.filter(e => e.chain === 'Long Châu');
  const vaccineEmps = filteredEmployees.filter(e => e.chain === 'Vaccine');

  // Halves for 2-Column mode
  const halfCount = Math.ceil(filteredEmployees.length / 2);
  const leftHalf = filteredEmployees.slice(0, halfCount);
  const rightHalf = filteredEmployees.slice(halfCount);

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
      setFormData({ id: '', insideCode: '', name: '', chain: 'FPT Shop', position: '', status: 'Active', startDate: '', note: '' });
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
        name: formData.name, 
        position: formData.position, 
        status: formData.status, 
        startDate: formData.startDate,
        note: formData.note
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

  return (
    <div className="w-full px-3.5 sm:px-6 py-2.5 sm:py-3.5 pb-8 relative z-10 animate-fade-in text-slate-800">
      
      {/* Top Header: Title, Metric Badges, Add Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-2.5">
        <div className="flex items-center gap-2.5 flex-wrap">
          <h1 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight shrink-0">
            Quản lý nhân viên
          </h1>
          
          {/* Quick Metrics Badges / Interactive Chain Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap text-xs">
            <button
              type="button"
              onClick={() => setChainFilter('All')}
              className={`px-2 py-0.5 rounded-lg font-bold transition-all cursor-pointer border text-[11.5px] ${
                chainFilter === 'All'
                  ? 'bg-slate-800 text-white border-slate-800 shadow-xs'
                  : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
              }`}
              title="Xem tất cả nhân sự"
            >
              Tổng: <span className="font-extrabold">{metrics.total}</span>
            </button>

            <button
              type="button"
              onClick={() => setChainFilter(chainFilter === 'FPT Shop' ? 'All' : 'FPT Shop')}
              className={`px-2 py-0.5 rounded-lg font-bold transition-all cursor-pointer border text-[11.5px] ${
                chainFilter === 'FPT Shop'
                  ? 'bg-orange-600 text-white border-orange-600 shadow-xs'
                  : 'bg-orange-50/90 hover:bg-orange-100 text-orange-700 border-orange-200/80'
              }`}
              title="Lọc nhân sự FPT Shop"
            >
              FPT Shop: <span className="font-extrabold">{metrics.fpt}</span>
            </button>

            <button
              type="button"
              onClick={() => setChainFilter(chainFilter === 'Long Châu' ? 'All' : 'Long Châu')}
              className={`px-2 py-0.5 rounded-lg font-bold transition-all cursor-pointer border text-[11.5px] ${
                chainFilter === 'Long Châu'
                  ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                  : 'bg-blue-50/90 hover:bg-blue-100 text-blue-700 border-blue-200/80'
              }`}
              title="Lọc nhân sự Long Châu"
            >
              Long Châu: <span className="font-extrabold">{metrics.longchau}</span>
            </button>

            <button
              type="button"
              onClick={() => setChainFilter(chainFilter === 'Vaccine' ? 'All' : 'Vaccine')}
              className={`px-2 py-0.5 rounded-lg font-bold transition-all cursor-pointer border text-[11.5px] ${
                chainFilter === 'Vaccine'
                  ? 'bg-purple-600 text-white border-purple-600 shadow-xs'
                  : 'bg-purple-50/90 hover:bg-purple-100 text-purple-700 border-purple-200/80'
              }`}
              title="Lọc nhân sự Vaccine"
            >
              Vaccine: <span className="font-extrabold">{metrics.vaccine}</span>
            </button>
          </div>
        </div>

        <button 
          type="button"
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-[12.5px] transition-colors shadow-sm cursor-pointer shrink-0 ml-auto sm:ml-0"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Thêm nhân viên</span>
        </button>
      </div>

      {/* Filters Bar & View Mode Toggle */}
      <div className="flex gap-2 sm:gap-2.5 mb-2.5 items-center flex-wrap">
        <div className="relative flex-1 min-w-[170px] max-w-sm">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Tìm Mã Inside, Mail, họ tên, note..." 
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-[12.5px]"
          />
        </div>
        
        <select 
          value={chainFilter}
          onChange={e => setChainFilter(e.target.value as any)}
          className="px-2.5 py-1 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-[12px] font-medium"
        >
          <option value="All">Tất cả chuỗi</option>
          <option value="FPT Shop">FPT Shop</option>
          <option value="Long Châu">Long Châu</option>
          <option value="Vaccine">Vaccine</option>
        </select>

        <select 
          value={sortBy}
          onChange={e => setSortBy(e.target.value as any)}
          className="px-2.5 py-1 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-[12px] font-medium"
        >
          <option value="insideCode">Xếp: Mã Inside</option>
          <option value="id">Xếp: Mail</option>
          <option value="name">Xếp: Tên</option>
          <option value="chain">Xếp: Chuỗi</option>
          <option value="startDate">Xếp: Ngày bắt đầu</option>
        </select>

        {/* View Mode Switcher */}
        <div className="flex items-center bg-slate-100 p-0.5 rounded-xl border border-slate-200 text-xs ml-auto">
          <button
            type="button"
            onClick={() => handleSetViewMode('by_chain')}
            className={`px-2 py-0.5 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1 text-[11.5px] ${
              viewMode === 'by_chain'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
            title="Song song 3 chuỗi (Hiển thị toàn bộ 38 nhân viên trên 1 màn hình không scroll)"
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">3 Chuỗi</span>
          </button>
          <button
            type="button"
            onClick={() => handleSetViewMode('two_columns')}
            className={`px-2 py-0.5 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1 text-[11.5px] ${
              viewMode === 'two_columns'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
            title="Chia đôi 2 cột (Hiển thị toàn bộ 38 nhân viên không scroll)"
          >
            <Columns className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">2 Cột</span>
          </button>
          <button
            type="button"
            onClick={() => handleSetViewMode('single')}
            className={`px-2 py-0.5 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1 text-[11.5px] ${
              viewMode === 'single'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
            title="Bảng đơn truyền thống"
          >
            <Table className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Bảng đơn</span>
          </button>
        </div>
      </div>

      {/* Main Table Content - Zero Scroll Layouts */}
      {viewMode === 'by_chain' && chainFilter === 'All' ? (
        /* 3 Columns Side-by-Side: FPT Shop (13), Long Châu (17), Vaccine (8) */
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
          {/* FPT Shop Column */}
          <div className="bg-white/95 border border-orange-200/80 rounded-2xl shadow-xs overflow-hidden flex flex-col">
            <div className="px-3 py-1.5 bg-orange-50/90 border-b border-orange-200/70 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                <span className="text-[12.5px] font-bold text-orange-950">FPT Shop</span>
              </div>
              <span className="text-[10.5px] font-extrabold px-2 py-0.5 rounded-md bg-orange-100 text-orange-800">
                {fptEmps.length} nhân sự
              </span>
            </div>
            <CompactEmployeeTable
              employees={fptEmps}
              showChainColumn={false}
              onEdit={openEditModal}
              onMove={openMoveModal}
              onSaveNote={handleSaveNote}
              loading={loading}
              emptyText="Không có nhân viên FPT Shop"
            />
          </div>

          {/* Long Châu Column */}
          <div className="bg-white/95 border border-blue-200/80 rounded-2xl shadow-xs overflow-hidden flex flex-col">
            <div className="px-3 py-1.5 bg-blue-50/90 border-b border-blue-200/70 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                <span className="text-[12.5px] font-bold text-blue-950">Long Châu</span>
              </div>
              <span className="text-[10.5px] font-extrabold px-2 py-0.5 rounded-md bg-blue-100 text-blue-800">
                {longchauEmps.length} nhân sự
              </span>
            </div>
            <CompactEmployeeTable
              employees={longchauEmps}
              showChainColumn={false}
              onEdit={openEditModal}
              onMove={openMoveModal}
              onSaveNote={handleSaveNote}
              loading={loading}
              emptyText="Không có nhân viên Long Châu"
            />
          </div>

          {/* Vaccine Column */}
          <div className="bg-white/95 border border-purple-200/80 rounded-2xl shadow-xs overflow-hidden flex flex-col">
            <div className="px-3 py-1.5 bg-purple-50/90 border-b border-purple-200/70 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                <span className="text-[12.5px] font-bold text-purple-950">Vaccine</span>
              </div>
              <span className="text-[10.5px] font-extrabold px-2 py-0.5 rounded-md bg-purple-100 text-purple-800">
                {vaccineEmps.length} nhân sự
              </span>
            </div>
            <CompactEmployeeTable
              employees={vaccineEmps}
              showChainColumn={false}
              onEdit={openEditModal}
              onMove={openMoveModal}
              onSaveNote={handleSaveNote}
              loading={loading}
              emptyText="Không có nhân viên Vaccine"
            />
          </div>
        </div>
      ) : viewMode === 'two_columns' && filteredEmployees.length > 8 ? (
        /* 2 Columns Side-by-Side: 19 & 19 */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <div className="bg-white/95 border border-slate-200/80 rounded-2xl shadow-xs overflow-hidden flex flex-col">
            <CompactEmployeeTable
              employees={leftHalf}
              showChainColumn={chainFilter === 'All'}
              onEdit={openEditModal}
              onMove={openMoveModal}
              onSaveNote={handleSaveNote}
              loading={loading}
            />
          </div>
          <div className="bg-white/95 border border-slate-200/80 rounded-2xl shadow-xs overflow-hidden flex flex-col">
            <CompactEmployeeTable
              employees={rightHalf}
              showChainColumn={chainFilter === 'All'}
              onEdit={openEditModal}
              onMove={openMoveModal}
              onSaveNote={handleSaveNote}
              loading={loading}
            />
          </div>
        </div>
      ) : (
        /* Single Full-Width Compact Table */
        <GlassCard className="overflow-hidden bg-white/95 border border-slate-200/80 rounded-2xl shadow-xs">
          <CompactEmployeeTable
            employees={filteredEmployees}
            showChainColumn={chainFilter === 'All'}
            onEdit={openEditModal}
            onMove={openMoveModal}
            onSaveNote={handleSaveNote}
            loading={loading}
          />
        </GlassCard>
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
              <div>
                <label className="block text-[13px] font-bold text-slate-700 mb-1">Thay đổi / Ghi chú</label>
                <input type="text" placeholder="Nhập ghi chú thay đổi nếu có..." value={formData.note} onChange={e => setFormData({...formData, note: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none"/>
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
                <div>
                  <label className="block text-[13px] font-bold text-slate-700 mb-1">Thay đổi / Ghi chú</label>
                  <input type="text" placeholder="Nhập ghi chú thay đổi..." value={formData.note} onChange={e => setFormData({...formData, note: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none"/>
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
                <span className="font-bold text-slate-900">{selectedEmployee.name} ({selectedEmployee.id})</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                <span className="text-slate-500 font-medium">Chuỗi hiện tại:</span>
                <span className="font-bold text-slate-900">{selectedEmployee.chain}</span>
              </div>
              <div>
                <label className="block text-slate-500 font-medium mb-2">Chuyển sang chuỗi mới:</label>
                <div className="grid grid-cols-2 gap-2">
                  {CHAINS.filter(c => c !== selectedEmployee.chain).map(c => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setMoveTarget(c)}
                      className={`p-3 rounded-xl border text-sm font-bold transition-all cursor-pointer ${
                        moveTarget === c 
                          ? 'border-emerald-600 bg-emerald-50 text-emerald-700 shadow-sm' 
                          : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 justify-end">
              <button type="button" onClick={() => setIsMoveModalOpen(false)} className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer">Hủy</button>
              <button type="button" onClick={handleMoveSubmit} className="px-5 py-2.5 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm cursor-pointer">Xác nhận chuyển</button>
            </div>
          </div>
        </div>,
        document.body
      )}

    </div>
  );
};

export default Employees;
