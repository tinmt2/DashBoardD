import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Search, Plus, Edit2, MoveRight, ShieldAlert, X } from 'lucide-react';
import { EmployeeService } from '../services/employeeService';
import type { Employee, Chain } from '../types';
import { GlassCard } from '../components/common/GlassCard';

const CHAINS: Chain[] = ['FPT Shop', 'Long Châu', 'Vaccine'];

const Employees: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [search, setSearch] = useState('');
  const [chainFilter, setChainFilter] = useState<Chain | 'All'>('All');
  const [statusFilter, setStatusFilter] = useState<'All' | 'Active' | 'Inactive'>('All');
  const [sortBy, setSortBy] = useState<'name' | 'id' | 'chain' | 'status'>('name');
  
  // Modals
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isMoveModalOpen, setIsMoveModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  
  // Form State
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    chain: 'FPT Shop' as Chain,
    position: '',
    status: 'Active' as 'Active' | 'Inactive',
    startDate: ''
  });
  const [formError, setFormError] = useState('');
  const [moveTarget, setMoveTarget] = useState<Chain>('FPT Shop');

  // Initial load only – no loading spinner on mutations
  useEffect(() => {
    EmployeeService.getEmployees().then(data => {
      setEmployees(data);
      setLoading(false);
    });
  }, []);

  // Helper: update a single employee in local state without reloading the whole list
  const updateLocalEmployee = (updated: Employee) => {
    setEmployees(prev => prev.map(e => e.id === updated.id ? updated : e));
  };

  const filteredEmployees = employees.filter(emp => {
    if (chainFilter !== 'All' && emp.chain !== chainFilter) return false;
    if (statusFilter !== 'All' && emp.status !== statusFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!emp.name.toLowerCase().includes(q) && !emp.id.toLowerCase().includes(q)) return false;
    }
    return true;
  }).sort((a, b) => {
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
      setFormData({ id: '', name: '', chain: 'FPT Shop', position: '', status: 'Active', startDate: '' });
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

  return (
    <div className="w-full px-8 lg:px-12 py-10 pb-16 relative z-10 animate-fade-in text-slate-800">
      
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-[28px] font-bold text-slate-900 tracking-tight">Quản lý nhân viên</h1>
        </div>
        <button 
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-[12px] font-bold text-[14px] transition-colors shadow-sm cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Thêm nhân viên
        </button>
      </div>

      {/* Metrics (Combined Bento Grid - Compact) */}
      <div className="w-full max-w-[580px]">
        <GlassCard className="flex items-center justify-between p-5 relative overflow-hidden mb-6 bg-white/60 shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-slate-200/60 rounded-2xl">
          {/* Left: Hero Metric */}
          <div className="relative z-10 pl-2">
            <div className="mb-2">
              <span className="text-[12px] font-bold text-slate-400 uppercase tracking-wider">Tổng nhân sự</span>
            </div>
            <div className="text-[54px] font-black text-slate-800 leading-none tracking-tight">{metrics.total}</div>
          </div>

          {/* Right: Sub metrics */}
          <div className="relative z-10 w-[240px] flex flex-col gap-2">
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

      {/* Filters */}
      <div className="flex gap-4 mb-6 items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Tìm kiếm theo Mail, họ tên..." 
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-[12px] border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-[14px]"
          />
        </div>
        <select 
          value={chainFilter}
          onChange={e => setChainFilter(e.target.value as any)}
          className="px-4 py-2 rounded-[12px] border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-[14px] font-medium"
        >
          <option value="All">Tất cả chuỗi</option>
          <option value="FPT Shop">FPT Shop</option>
          <option value="Long Châu">Long Châu</option>
          <option value="Vaccine">Vaccine</option>
        </select>
        
        <select 
          value={sortBy}
          onChange={e => setSortBy(e.target.value as any)}
          className="px-4 py-2 rounded-[12px] border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-[14px] font-medium ml-auto"
        >
          <option value="id">Sắp xếp theo Mail</option>
          <option value="chain">Sắp xếp theo Chuỗi</option>
          <option value="startDate">Sắp xếp theo Ngày bắt đầu</option>
        </select>
      </div>

      {/* Table */}
      <GlassCard className="overflow-hidden bg-white/80">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200">
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
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-500 font-medium">Đang tải danh sách nhân viên...</td>
                </tr>
              ) : filteredEmployees.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-500 font-medium">Không tìm thấy nhân viên phù hợp</td>
                </tr>
              ) : (
                filteredEmployees.map((emp) => (
                  <tr key={emp.id} className="hover:bg-slate-50/50 transition-colors">
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
                          onClick={() => { setSelectedEmployee(emp); setFormData({...formData, name: emp.name, position: emp.position || '', status: emp.status, startDate: emp.startDate || ''}); setIsEditModalOpen(true); }}
                          className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
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
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
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

      {/* Add Employee Modal */}
      {isAddModalOpen && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-[24px] p-8 w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-slate-900">Thêm nhân viên mới</h2>
              <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5"/></button>
            </div>
            
            {formError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-100 text-rose-600 rounded-lg text-sm flex gap-2 items-center">
                <ShieldAlert className="w-4 h-4" /> {formError}
              </div>
            )}

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-[13px] font-bold text-slate-700 mb-1">Mail *</label>
                <input required type="text" value={formData.id} onChange={e => setFormData({...formData, id: e.target.value})} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500/50 outline-none"/>
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
                <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors">Hủy</button>
                <button type="submit" className="px-5 py-2.5 rounded-xl font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-sm">Thêm nhân viên</button>
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
                  <button type="button" onClick={() => setIsDeleteConfirmOpen(false)} className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors">Quay lại</button>
                  <button 
                    type="button" 
                    onClick={() => {
                      setEmployees(prev => prev.filter(e => e.id !== selectedEmployee.id));
                      EmployeeService.deleteEmployee(selectedEmployee.id);
                      setIsDeleteConfirmOpen(false);
                      setIsEditModalOpen(false);
                      setSelectedEmployee(null);
                    }}
                    className="px-5 py-2.5 rounded-xl font-bold text-white bg-rose-600 hover:bg-rose-700 transition-colors shadow-sm"
                  >
                    Xác nhận xóa
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleEditSubmit} className="space-y-4">
                <div>
                  <label className="block text-[13px] font-bold text-slate-700 mb-1">Mail (Không thể đổi)</label>
                  <input disabled type="text" value={selectedEmployee.id} className="w-full px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-500 cursor-not-allowed outline-none"/>
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
                    className="px-4 py-2.5 rounded-xl font-bold text-rose-600 hover:bg-rose-50 border border-rose-200 transition-colors text-[13px]"
                  >
                    Xóa nhân viên
                  </button>
                  <div className="flex gap-3">
                    <button type="button" onClick={() => setIsEditModalOpen(false)} className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors">Hủy</button>
                    <button type="submit" className="px-5 py-2.5 rounded-xl font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors shadow-sm">Lưu thay đổi</button>
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
                  className="px-4 py-2 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500/50 outline-none font-bold text-emerald-700"
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
              <button onClick={() => setIsMoveModalOpen(false)} className="px-5 py-2.5 rounded-xl font-bold text-slate-600 hover:bg-slate-100 transition-colors">Hủy</button>
              <button onClick={handleMoveSubmit} className="px-5 py-2.5 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm">Xác nhận chuyển</button>
            </div>
          </div>
        </div>,
        document.body
      )}

    </div>
  );
};

export default Employees;


