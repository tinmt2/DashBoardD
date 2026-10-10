// ─── Domain Types ────────────────────────────────────────────────────────────

/** Ba chuỗi được giám sát */
export type Chain = 'FPT Shop' | 'Long Châu' | 'Vaccine';

/** Loại lỗi Calllog / Ticket */
export type CalllogErrorType =
  | 'Thiếu thông tin'
  | 'Sai nội dung'
  | 'Sai phân loại'
  | 'Sai quy trình'
  | 'Thiếu bằng chứng'
  | 'Khác';

export type TimeRange = '24h' | '7d' | '30d';

// ─── Employee ────────────────────────────────────────────────────────────────

export interface Employee {
  id: string;
  name: string;
  chain: Chain;
  status: 'Active' | 'Inactive';
  
  /** Tổng số lỗi Calllog/Ticket */
  totalErrors: number;
  /** Tổng số Calllog/Ticket đã kiểm tra */
  totalChecked: number;
  /** Thời điểm hoạt động gần nhất */
  lastActivity: string;
  
  position?: string;
  startDate?: string;
  createdAt?: string;
  updatedAt?: string;
}

// ─── Employee Transfer History ────────────────────────────────────────────────

export interface EmployeeTransferHistory {
  employeeId: string;
  fromChain: Chain;
  toChain: Chain;
  transferredAt: string;
  transferredBy?: string;
}

// ─── Calllog / Ticket Error Record ───────────────────────────────────────────

export interface CalllogError {
  id: string;
  employeeId: string;
  employeeName: string;
  chain: Chain;
  /** Loại lỗi trong Calllog/Ticket */
  errorType: CalllogErrorType;
  /** Số lỗi trong bản ghi này */
  errorCount: number;
  /** Ngày phát hiện lỗi */
  detectedAt: string;
  /** Nội dung mô tả ngắn */
  note: string;
}

// ─── Overview Summary ────────────────────────────────────────────────────────

/** Tổng hợp KPI cho màn hình Tổng quan */
export interface CalllogOverviewSummary {
  /** Tổng số lỗi Calllog/Ticket trong kỳ */
  totalErrors: number;
  /** Tổng số Calllog/Ticket đã kiểm tra */
  totalChecked: number;
  /** Tỷ lệ lỗi = totalErrors / totalChecked */
  errorRate: number;
  /** Số nhân viên có ít nhất 1 lỗi */
  employeesWithErrors: number;
  /** Tổng nhân viên */
  totalEmployees: number;
}

// ─── Chain Stats ─────────────────────────────────────────────────────────────

export interface ChainCalllogStats {
  chain: Chain;
  /** Số lỗi trong kỳ */
  totalErrors: number;
  /** Số Calllog/Ticket đã kiểm tra */
  totalChecked: number;
  /** Tỷ lệ lỗi */
  errorRate: number;
  /** Màu nhận diện chuỗi */
  color: string;
}

// ─── Error Type Stats ────────────────────────────────────────────────────────

export interface CalllogErrorTypeStats {
  type: CalllogErrorType;
  count: number;
}

// ─── Employee Error Ranking ──────────────────────────────────────────────────

export interface EmployeeErrorRanking {
  employeeId: string;
  name: string;
  chain: Chain;
  totalErrors: number;
  totalChecked: number;
}

// ─── Legacy types kept for compatibility with api.ts ─────────────────────────

/** @deprecated */
export interface InternalError {
  id: string;
  employeeId: string;
  chain: Chain;
  type: string;
  status: string;
  createdAt: string;
  resolvedAt?: string;
  description: string;
}

/** @deprecated */
export interface Metric {
  label: string;
  value: string | number;
  change: number;
  sparkline: { time: string; value: number }[];
}

/** @deprecated */
export interface TaskDistribution {
  status: string;
  count: number;
  color: string;
}

/** @deprecated */
export interface DashboardSummary {
  totalErrorsMetric: Metric;
  pendingErrorsMetric: Metric;
  resolvedErrorsMetric: Metric;
  taskDistribution: TaskDistribution[];
}

/** @deprecated */
export interface ErrorTrend {
  date: string;
  systemErrors: number;
  resolved: number;
}

/** @deprecated */
export interface ChainSummary {
  chain: Chain;
  summary: DashboardSummary;
}

/** @deprecated */
export interface ChainErrorStats {
  chain: Chain;
  totalErrors: number;
  pendingErrors: number;
  resolvedErrors: number;
  color: string;
}

/** @deprecated */
export interface ErrorTypeStats {
  type: string;
  count: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
}
