from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class LongChauChainStats(BaseModel):
    total: int
    errors: int
    errorRate: float

from typing import List

class ErrorEmployee(BaseModel):
    name: str
    count: int

class LongChauErrorTypeStat(BaseModel):
    errorType: str
    count: int
    employees: List[ErrorEmployee] = []

class LongChauEmployeeStat(BaseModel):
    employeeName: str
    errorCount: int
    statusStats: Dict[str, int] = {}
    totalReminders: int = 0

class LongChauShopStat(BaseModel):
    shopCode: Optional[str]
    shopName: Optional[str]
    errorCount: int

class LongChauRegionStat(BaseModel):
    region: Optional[str]
    errorCount: int

class LongChauDashboardData(BaseModel):
    totalChecked: int
    totalErrors: int
    errorRate: float
    totalEmployees: int
    employeesWithErrors: int
    totalShops: int
    totalReminders: int = 0
    chainStats: LongChauChainStats
    errorTypeStats: List[LongChauErrorTypeStat]
    employeeErrorRanking: List[LongChauEmployeeStat]
    shopErrorRanking: List[LongChauShopStat]
    regionErrorStats: List[LongChauRegionStat]
    ticketStatusStats: List[Dict[str, Any]] = []

class LongChauDashboardSummaryResponse(BaseModel):
    success: bool
    chain: str = "Long Châu"
    data: LongChauDashboardData
