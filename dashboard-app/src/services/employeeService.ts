import { dashboardSummary, errorTrends, chainSummaries, mockEmployees } from './mockData';
import type { Chain, Employee, DashboardSummary, ErrorTrend, EmployeeTransferHistory } from '../types';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
const STORAGE_KEY = 'dashboard_employees_v2'; // bump version to reset old mock data
const HISTORY_STORAGE_KEY = 'dashboard_employee_history';

// Initialize localStorage with mock data if empty
if (!localStorage.getItem(STORAGE_KEY)) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(mockEmployees));
}

const getStoredEmployees = (): Employee[] => {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
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
  localStorage.setItem(STORAGE_KEY, JSON.stringify(employees));
  // Dispatch a custom event to notify other modules of data changes
  window.dispatchEvent(new Event('employees_updated'));
};

export const DashboardService = {
  getSummary: async (chain?: Chain): Promise<DashboardSummary> => {
    await delay(300);
    if (chain && chainSummaries[chain]) {
      return chainSummaries[chain].summary;
    }
    return dashboardSummary;
  },
  
  getTrends: async (chain?: Chain): Promise<ErrorTrend[]> => {
    await delay(400);
    return errorTrends;
  }
};

export const EmployeeService = {
  getEmployees: async (chain?: Chain): Promise<Employee[]> => {
    await delay(200); // reduced delay for better UX
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
    await delay(200);
    const employees = getStoredEmployees();
    
    // Check for duplicate ID
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
  },

  updateEmployee: async (employee: Employee): Promise<Employee> => {
    await delay(200);
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
  },

  moveEmployee: async (employeeId: string, targetChain: Chain): Promise<Employee> => {
    await delay(200);
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
  },

  getEmployeeHistory: async (employeeId: string): Promise<EmployeeTransferHistory[]> => {
    await delay(100);
    return getStoredHistory()
      .filter(h => h.employeeId === employeeId)
      .sort((a, b) => new Date(b.transferredAt).getTime() - new Date(a.transferredAt).getTime());
  },

  deactivateEmployee: async (employeeId: string): Promise<Employee> => {
    await delay(200);
    const employees = getStoredEmployees();
    const index = employees.findIndex(e => e.id === employeeId);
    
    if (index === -1) {
      throw new Error('Không tìm thấy nhân viên');
    }

    employees[index] = {
      ...employees[index],
      status: 'Inactive',
      updatedAt: new Date().toISOString(),
    };

    saveEmployees(employees);
    return employees[index];
  },

  deleteEmployee: async (employeeId: string): Promise<void> => {
    await delay(100);
    const employees = getStoredEmployees().filter(e => e.id !== employeeId);
    saveEmployees(employees);
  }
};

