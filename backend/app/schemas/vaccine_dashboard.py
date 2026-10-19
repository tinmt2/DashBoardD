from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class VaccineChainStats(BaseModel):
    total: int
    errors: int
    errorRate: float

from typing import List

class ErrorEmployee(BaseModel):
    name: str
    count: int

class VaccineErrorTypeStat(BaseModel):
    errorType: str
    count: int
    employees: List[ErrorEmployee] = []

class VaccineEmployeeStat(BaseModel):
    employeeName: str
    errorCount: int
    statusStats: Dict[str, int] = {}
    totalReminders: int = 0

class VaccineShopStat(BaseModel):
    shopCode: Optional[str]
    shopName: Optional[str]
    errorCount: int

class VaccineRegionStat(BaseModel):
    region: Optional[str]
    errorCount: int

class VaccineDashboardData(BaseModel):
    totalChecked: int
    totalErrors: int
    errorRate: float
    totalEmployees: int
    employeesWithErrors: int
    totalShops: int
    totalReminders: int = 0
    nonPenaltyCount: int = 0
    penaltyCount: int = 0
    summaryStats: List[Dict[str, Any]] = []
    chainStats: VaccineChainStats
    errorTypeStats: List[VaccineErrorTypeStat]
    employeeErrorRanking: List[VaccineEmployeeStat]
    shopErrorRanking: List[VaccineShopStat]
    regionErrorStats: List[VaccineRegionStat]
    ticketStatusStats: List[Dict[str, Any]] = []

class VaccineDashboardSummaryResponse(BaseModel):
    success: bool
    chain: str = "Vaccine"
    data: VaccineDashboardData
