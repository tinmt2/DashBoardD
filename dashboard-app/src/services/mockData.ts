import type {
  Chain,
  Employee,
  CalllogError,
  CalllogErrorType,
  DashboardSummary,
  ErrorTrend,
  ChainSummary,
  TaskDistribution,
  ChainErrorStats,
  ErrorTypeStats,
  CalllogOverviewSummary,
  ChainCalllogStats,
  CalllogErrorTypeStats,
  EmployeeErrorRanking,
} from '../types';

// ─── Employees ─────────────────────────────────────────────────────────────
// Danh sách nhân viên thực tế – chuỗi sẽ được gán thủ công trong Settings

export const mockEmployees: Employee[] = [
  { id: 'LuanNV8',     name: 'Nguyễn Văn Luân',         chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'MinhPP2',     name: 'Phạm Phú Minh',           chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'QuyNN13',     name: 'Nguyễn Ngọc Quý',         chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'TanTQ6',      name: 'Trần Quang Tân',           chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'TuongPN3',    name: 'Phan Ngọc Tường',          chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'BaoTDC',      name: 'Trần Đức Chí Bảo',        chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'SonDQ3',      name: 'Đặng Quang Sơn',           chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'DucNM79',     name: 'Nguyễn Minh Đức',          chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'ViDNT2',      name: 'Đỗ Ngọc Thúy Vi',          chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'DuyenNTM20',  name: 'Nguyễn Thị Mỹ Duyên',     chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'SangLM4',     name: 'Lê Minh Sáng',             chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'TamNT54',     name: 'Nguyễn Thanh Tâm',         chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'SonTCH',      name: 'Trần Công Hoàng Sơn',      chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'ThanhNN25',   name: 'Nguyễn Ngọc Thanh',        chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'QuyNV34',     name: 'Nguyễn Văn Quý',           chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'TaiVM3',      name: 'Võ Minh Tài',              chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'ThongHQ3',    name: 'Hồ Quốc Thông',            chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'DatCT10',     name: 'Chiêng Tấn Đạt',           chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'PhongTTH2',   name: 'Trần Trương Huy Phong',    chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'HienPN3',     name: 'Phạm Ngọc Hiền',           chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'DuongNP',     name: 'Nguyễn Phi Dương',         chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'LinhLT47',    name: 'Lý Thành Linh',            chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'DuanHX',      name: 'Hoàng Xuân Duẩn',          chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'NhanDT27',    name: 'Dương Thành Nhân',          chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'TuNM35',      name: 'Nguyễn Minh Tú',           chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'TamNM25',     name: 'Nguyễn Minh Tâm',          chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'VyTTH6',      name: 'Tạ Trần Hà Vy',            chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'MyPTK4',      name: 'Phạm Thị Kiều My',         chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'NgocTB35',    name: 'Trác Bảo Ngọc',            chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'TamLM10',     name: 'Lê Minh Tâm',              chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'SonTT37',     name: 'Trần Thiện Sơn',           chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'AnHSH2',      name: 'Hứa Sang Hoàng Ân',        chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
  { id: 'DinhLV8',     name: 'Lý Văn Định',              chain: 'FPT Shop', status: 'Active', totalErrors: 0, totalChecked: 0, lastActivity: '' },
];

// ─── Calllog / Ticket Error Records ────────────────────────────────────────
// Đây là các bản ghi lỗi tìm thấy khi kiểm tra Calllog/Ticket của nhân viên

export const mockCalllogErrors: CalllogError[] = [
  { id: 'CL001', employeeId: 'EMP012', employeeName: 'Lý Thị Minh',    chain: 'FPT Shop',  errorType: 'Thiếu thông tin',  errorCount: 12, detectedAt: '2026-09-28T09:00:00Z', note: 'Thiếu số điện thoại khách hàng trong 12 calllog' },
  { id: 'CL002', employeeId: 'EMP001', employeeName: 'Nguyễn Văn An',  chain: 'FPT Shop',  errorType: 'Sai nội dung',     errorCount:  8, detectedAt: '2026-09-28T09:30:00Z', note: 'Nội dung mô tả không khớp với phân loại' },
  { id: 'CL003', employeeId: 'EMP005', employeeName: 'Hoàng Văn Em',   chain: 'Long Châu', errorType: 'Sai quy trình',    errorCount: 11, detectedAt: '2026-09-28T10:00:00Z', note: 'Không theo quy trình xử lý khiếu nại' },
  { id: 'CL004', employeeId: 'EMP022', employeeName: 'Hoàng Thị Yến',  chain: 'FPT Shop',  errorType: 'Thiếu bằng chứng', errorCount:  9, detectedAt: '2026-09-28T10:30:00Z', note: 'Không đính kèm ảnh minh chứng trong ticket' },
  { id: 'CL005', employeeId: 'EMP003', employeeName: 'Lê Văn Cường',   chain: 'Vaccine',   errorType: 'Sai phân loại',    errorCount:  7, detectedAt: '2026-09-28T11:00:00Z', note: 'Phân loại sai nhóm dịch vụ vaccine' },
  { id: 'CL006', employeeId: 'EMP010', employeeName: 'Đinh Thị Kim',   chain: 'Long Châu', errorType: 'Thiếu thông tin',  errorCount:  6, detectedAt: '2026-09-28T11:30:00Z', note: 'Thiếu ngày hẹn tái khám trong ticket' },
  { id: 'CL007', employeeId: 'EMP014', employeeName: 'Tô Thị Oanh',    chain: 'FPT Shop',  errorType: 'Sai nội dung',     errorCount:  5, detectedAt: '2026-09-28T12:00:00Z', note: 'Mô tả sự cố không đúng với thực tế' },
  { id: 'CL008', employeeId: 'EMP006', employeeName: 'Ngô Thị Phương', chain: 'FPT Shop',  errorType: 'Sai quy trình',    errorCount:  4, detectedAt: '2026-09-28T13:00:00Z', note: 'Không ghi nhận phản hồi khách hàng' },
  { id: 'CL009', employeeId: 'EMP019', employeeName: 'Nguyễn Văn Uy',  chain: 'Long Châu', errorType: 'Thiếu bằng chứng', errorCount:  6, detectedAt: '2026-09-28T13:30:00Z', note: 'Thiếu chữ ký xác nhận từ khách hàng' },
  { id: 'CL010', employeeId: 'EMP021', employeeName: 'Phạm Văn Xuân',  chain: 'Vaccine',   errorType: 'Thiếu thông tin',  errorCount:  5, detectedAt: '2026-09-28T14:00:00Z', note: 'Thiếu thông tin tiêm chủng trong calllog' },
];

// ─── Calllog Overview Summary ──────────────────────────────────────────────

export const calllogOverviewSummary: CalllogOverviewSummary = {
  totalErrors:        872,
  totalChecked:       4_560,
  errorRate:          19.1,   // %
  employeesWithErrors: 18,
  totalEmployees:      25,
};

// ─── Chain Calllog Stats ───────────────────────────────────────────────────

export const chainCalllogStats: ChainCalllogStats[] = [
  { chain: 'FPT Shop',  totalErrors: 420, totalChecked: 2100, errorRate: 20.0, color: '#f87171' },
  { chain: 'Long Châu', totalErrors: 285, totalChecked: 1520, errorRate: 18.8, color: '#60a5fa' },
  { chain: 'Vaccine',   totalErrors: 167, totalChecked:  940, errorRate: 17.8, color: '#34d399' },
];

// ─── Calllog Error Type Stats ──────────────────────────────────────────────

export const calllogErrorTypeStats: CalllogErrorTypeStats[] = [
  { type: 'Thiếu thông tin',  count: 284 },
  { type: 'Sai nội dung',     count: 192 },
  { type: 'Sai phân loại',    count: 145 },
  { type: 'Sai quy trình',    count: 104 },
  { type: 'Thiếu bằng chứng', count:  87 },
  { type: 'Khác',             count:  60 },
];

// ─── Employee Error Ranking ────────────────────────────────────────────────

export const employeeErrorRanking: EmployeeErrorRanking[] = mockEmployees
  .filter(e => e.totalErrors > 0)
  .sort((a, b) => b.totalErrors - a.totalErrors)
  .slice(0, 8)
  .map(e => ({
    employeeId:  e.id,
    name:        e.name,
    chain:       e.chain,
    totalErrors: e.totalErrors,
    totalChecked: e.totalChecked,
  }));

// ─── Legacy exports (used by api.ts / existing pages) ─────────────────────

const generateSparkline = (base: number, variance: number, length = 10) => {
  return Array.from({ length }, (_, i) => ({
    time: `T${i}`,
    value: Math.max(0, base + (Math.random() * variance * 2 - variance))
  }));
};

export const dashboardSummary: DashboardSummary = {
  totalErrorsMetric:   { label: 'Tổng số lỗi',   value: '872',   change: -4.2,  sparkline: generateSparkline(900,  30) },
  pendingErrorsMetric: { label: 'Lỗi chưa xử lý', value: '162',   change: -12.1, sparkline: generateSparkline(180,  20) },
  resolvedErrorsMetric:{ label: 'Lỗi đã xử lý',  value: '2.683', change:  8.5,  sparkline: generateSparkline(2500, 150) },
  taskDistribution: [],
};

export const errorTrends: ErrorTrend[] = [
  { date: '01/09', systemErrors: 120, resolved: 100 },
  { date: '02/09', systemErrors: 132, resolved: 110 },
  { date: '03/09', systemErrors: 101, resolved:  90 },
  { date: '04/09', systemErrors: 145, resolved: 130 },
  { date: '05/09', systemErrors: 160, resolved: 145 },
  { date: '06/09', systemErrors: 110, resolved: 100 },
  { date: '07/09', systemErrors: 104, resolved:  95 },
];

export const chainSummaries: Record<Chain, ChainSummary> = {
  'FPT Shop': {
    chain: 'FPT Shop',
    summary: {
      totalErrorsMetric:   { label: 'Tổng số lỗi', value: '420', change: -2.1, sparkline: generateSparkline(430, 20) },
      pendingErrorsMetric: { label: 'Chưa xử lý',  value: '54',  change: -8.5, sparkline: generateSparkline(60,  10) },
      resolvedErrorsMetric:{ label: 'Đã xử lý',    value: '366', change:  4.8, sparkline: generateSparkline(350, 20) },
      taskDistribution: [],
    }
  },
  'Long Châu': {
    chain: 'Long Châu',
    summary: {
      totalErrorsMetric:   { label: 'Tổng số lỗi', value: '285', change: -5.4, sparkline: generateSparkline(300, 15) },
      pendingErrorsMetric: { label: 'Chưa xử lý',  value: '80',  change: -15.1, sparkline: generateSparkline(95, 10) },
      resolvedErrorsMetric:{ label: 'Đã xử lý',    value: '205', change: 10.2, sparkline: generateSparkline(190, 15) },
      taskDistribution: [],
    }
  },
  'Vaccine': {
    chain: 'Vaccine',
    summary: {
      totalErrorsMetric:   { label: 'Tổng số lỗi', value: '167', change: 1.5,  sparkline: generateSparkline(160, 10) },
      pendingErrorsMetric: { label: 'Chưa xử lý',  value: '28',  change: -6.4, sparkline: generateSparkline(32,  5)  },
      resolvedErrorsMetric:{ label: 'Đã xử lý',    value: '139', change:  2.1, sparkline: generateSparkline(135, 8)  },
      taskDistribution: [],
    }
  }
};

/** @deprecated */
export const chainErrorStats: ChainErrorStats[] = [
  { chain: 'FPT Shop',  totalErrors: 420, pendingErrors: 54, resolvedErrors: 366, color: '#f87171' },
  { chain: 'Long Châu', totalErrors: 285, pendingErrors: 80, resolvedErrors: 205, color: '#60a5fa' },
  { chain: 'Vaccine',   totalErrors: 167, pendingErrors: 28, resolvedErrors: 139, color: '#34d399' },
];

/** @deprecated — use calllogErrorTypeStats */
export const errorTypeStats: ErrorTypeStats[] = [
  { type: 'Thiếu thông tin',  count: 284, severity: 'critical' },
  { type: 'Sai nội dung',     count: 192, severity: 'high'     },
  { type: 'Sai phân loại',    count: 145, severity: 'high'     },
  { type: 'Sai quy trình',    count: 104, severity: 'medium'   },
  { type: 'Thiếu bằng chứng', count:  87, severity: 'medium'   },
  { type: 'Khác',             count:  60, severity: 'low'      },
];

// Keep mockErrors for backwards compat with Employee page
export const mockErrors = mockCalllogErrors.map(c => ({
  id: c.id, employeeId: c.employeeId, chain: c.chain,
  type: 'Khác' as const, status: 'Chưa xử lý' as const,
  createdAt: c.detectedAt, description: c.note,
}));
