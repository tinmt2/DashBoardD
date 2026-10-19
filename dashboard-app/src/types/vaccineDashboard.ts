export interface ErrorTypeStat {
  errorType: string;
  count: number;
}

export interface EmployeeErrorRanking {
  employeeName: string;
  errorCount: number;
}

export interface ShopErrorRanking {
  shopCode: string;
  shopName: string;
  errorCount: number;
}

export interface RegionErrorStat {
  region: string;
  errorCount: number;
}

export interface VaccineDashboardSummary {
  totalChecked: number;
  totalErrors: number;
  errorRate: number;
  totalEmployees: number;
  employeesWithErrors: number;
  totalShops: number;

  chainStats: {
    total: number;
    errors: number;
    errorRate: number;
  };

  errorTypeStats: ErrorTypeStat[];
  employeeErrorRanking: EmployeeErrorRanking[];
  shopErrorRanking: ShopErrorRanking[];
  regionErrorStats: RegionErrorStat[];
  nonPenaltyCount?: number;
  penaltyCount?: number;
  summaryStats?: Array<{ status: string; count: number }>;
}

export interface VaccineDashboardResponse {
  success: boolean;
  chain: string;
  data: VaccineDashboardSummary;
}
