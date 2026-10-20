import { dashboardSummary, errorTrends, chainSummaries, mockEmployees } from './mockData';
import type { Chain, Employee, DashboardSummary, ErrorTrend, EmployeeTransferHistory } from '../types';
import { API_BASE_URL } from './apiConfig';

const STORAGE_KEY = 'dashboard_employees_v2';
const HISTORY_STORAGE_KEY = 'dashboard_employee_history';

// Initialize localStorage with mock data if empty
if (!localStorage.getItem(STORAGE_KEY)) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(mockEmployees));
}

let memoryEmployees: Employee[] | null = null;

const getStoredEmployees = (): Employee[] => {
  if (memoryEmployees) return memoryEmployees;
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    memoryEmployees = data ? JSON.parse(data) : [];
    return memoryEmployees || [];
  } catch (error) {
    console.error("Failed to parse stored employees", error);
    return [];
  }
};

const getStoredHistory = (): EmployeeTransferHistory[] => {
  try {
    const data = localStorage.getItem(HISTORY_STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    return [];
  }
};

const addHistoryRecord = (record: EmployeeTransferHistory) => {
  const history = getStoredHistory();
  history.push(record);
  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
};

const saveEmployees = (employees: Employee[]) => {
  memoryEmployees = employees;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(employees));
  // Dispatch a custom event to notify other modules of data changes
  window.dispatchEvent(new Event('employees_updated'));
};

export const DashboardService = {
  getSummary: async (chain?: Chain): Promise<DashboardSummary> => {
    if (chain && chainSummaries[chain]) {
      return chainSummaries[chain].summary;
    }
    return dashboardSummary;
  },
  
  getTrends: async (chain?: Chain): Promise<ErrorTrend[]> => {
    return errorTrends;
  }
};

export const EmployeeService = {
  getEmployees: async (chain?: Chain): Promise<Employee[]> => {
    try {
      const url = chain 
        ? `${API_BASE_URL}/api/employees?chain=${encodeURIComponent(chain)}`
        : `${API_BASE_URL}/api/employees`;
      const res = await fetch(url);
      if (res.ok) {
        const data: Employee[] = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          if (!chain) {
            saveEmployees(data);
          }
          return data;
        }
      }
    } catch (e) {
      console.warn("Could not fetch employees from server, using local storage", e);
    }
    const employees = getStoredEmployees();
    if (chain) {
      return employees.filter(e => e.chain === chain);
    }
    return employees;
  },

  getActiveEmployees: async (chain?: Chain): Promise<Employee[]> => {
    const employees = await EmployeeService.getEmployees(chain);
    return employees.filter(e => e.status === 'Active');
  },

  getEmployeesByChain: async (chain: Chain): Promise<Employee[]> => {
    return EmployeeService.getEmployees(chain);
  },

  createEmployee: async (employeeData: Omit<Employee, 'totalErrors' | 'totalChecked' | 'lastActivity'>): Promise<Employee> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(employeeData)
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Lỗi khi thêm nhân viên' }));
        throw new Error(err.detail || 'Lỗi khi thêm nhân viên');
      }
      const newEmployee: Employee = await res.json();
      const employees = getStoredEmployees();
      saveEmployees([newEmployee, ...employees.filter(e => e.id !== newEmployee.id)]);
      return newEmployee;
    } catch (err: any) {
      if (err.message && err.message.includes('Mã nhân viên đã tồn tại')) {
        throw err;
      }
      console.warn("Backend create failed, fallback to local", err);
      const employees = getStoredEmployees();
      if (employees.some(e => e.id === employeeData.id)) {
        throw new Error('Mã nhân viên đã tồn tại');
      }

      const newEmployee: Employee = {
        ...employeeData,
        totalErrors: 0,
        totalChecked: 0,
        lastActivity: new Date().toISOString(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      employees.unshift(newEmployee);
      saveEmployees(employees);
      return newEmployee;
    }
  },

  updateEmployee: async (employee: Employee): Promise<Employee> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/${encodeURIComponent(employee.id)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: employee.name,
          chain: employee.chain,
          position: employee.position,
          status: employee.status,
          startDate: employee.startDate
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Lỗi khi cập nhật nhân viên' }));
        throw new Error(err.detail || 'Lỗi khi cập nhật nhân viên');
      }
      const updated: Employee = await res.json();
      const employees = getStoredEmployees();
      const idx = employees.findIndex(e => e.id === updated.id);
      if (idx !== -1) {
        employees[idx] = updated;
      } else {
        employees.push(updated);
      }
      saveEmployees(employees);
      return updated;
    } catch (err: any) {
      console.warn("Backend update failed, fallback to local", err);
      const employees = getStoredEmployees();
      const index = employees.findIndex(e => e.id === employee.id);
      
      if (index === -1) {
        throw new Error('Không tìm thấy nhân viên');
      }

      employees[index] = {
        ...employees[index],
        ...employee,
        updatedAt: new Date().toISOString(),
      };

      saveEmployees(employees);
      return employees[index];
    }
  },

  moveEmployee: async (employeeId: string, targetChain: Chain): Promise<Employee> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/${encodeURIComponent(employeeId)}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targetChain })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Lỗi khi điều chuyển' }));
        throw new Error(err.detail || 'Lỗi khi điều chuyển');
      }
      const updated: Employee = await res.json();
      const employees = getStoredEmployees();
      const idx = employees.findIndex(e => e.id === updated.id);
      const fromChain = idx !== -1 ? employees[idx].chain : 'FPT Shop';
      if (idx !== -1) {
        employees[idx] = updated;
      }
      saveEmployees(employees);
      addHistoryRecord({
        employeeId,
        fromChain,
        toChain: targetChain,
        transferredAt: new Date().toISOString()
      });
      return updated;
    } catch (err: any) {
      console.warn("Backend move failed, fallback to local", err);
      const employees = getStoredEmployees();
      const index = employees.findIndex(e => e.id === employeeId);
      
      if (index === -1) {
        throw new Error('Không tìm thấy nhân viên');
      }

      if (employees[index].chain === targetChain) {
        throw new Error('Nhân viên đã ở chuỗi này');
      }

      const fromChain = employees[index].chain;
      
      employees[index] = {
        ...employees[index],
        chain: targetChain,
        updatedAt: new Date().toISOString(),
      };

      saveEmployees(employees);
      addHistoryRecord({
        employeeId,
        fromChain,
        toChain: targetChain,
        transferredAt: new Date().toISOString()
      });
      
      return employees[index];
    }
  },

  getEmployeeHistory: async (employeeId: string): Promise<EmployeeTransferHistory[]> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/employees/${encodeURIComponent(employeeId)}/history`);
      if (res.ok) {
        const history: EmployeeTransferHistory[] = await res.json();
        if (Array.isArray(history) && history.length > 0) {
          return history;
        }
      }
    } catch (e) {
      console.warn("Backend get history failed, fallback to local", e);
    }
    return getStoredHistory()
      .filter(h => h.employeeId === employeeId)
      .sort((a, b) => new Date(b.transferredAt).getTime() - new Date(a.transferredAt).getTime());
  },

  deactivateEmployee: async (employeeId: string): Promise<Employee> => {
    const current = getStoredEmployees().find(e => e.id === employeeId);
    if (!current) {
      throw new Error('Không tìm thấy nhân viên');
    }
    return EmployeeService.updateEmployee({
      ...current,
      status: 'Inactive'
    });
  },

  deleteEmployee: async (employeeId: string): Promise<void> => {
    try {
      await fetch(`${API_BASE_URL}/api/employees/${encodeURIComponent(employeeId)}`, {
        method: 'DELETE'
      });
    } catch (e) {
      console.warn("Backend delete failed", e);
    }
    const employees = getStoredEmployees().filter(e => e.id !== employeeId);
    saveEmployees(employees);
  }
};
