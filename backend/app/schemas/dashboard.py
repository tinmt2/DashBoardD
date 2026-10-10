from pydantic import BaseModel
from typing import List, Optional

class CalllogOverviewSummary(BaseModel):
    totalErrors: int
    totalChecked: int
    statusStats: Optional[dict] = None
    errorRate: float
    employeesWithErrors: int
    totalEmployees: int
    totalReminders: int

class ChainCalllogStats(BaseModel):
    chain: str
    totalErrors: int
    totalChecked: int
    statusStats: Optional[dict] = None
    errorRate: float
    color: str

class ErrorEmployee(BaseModel):
    name: str
    count: int

class CalllogErrorTypeStats(BaseModel):
    type: str
    count: int
    employees: List[ErrorEmployee] = []

class TicketStatusStats(BaseModel):
    status: str
    count: int

class EmployeeErrorRanking(BaseModel):
    employeeId: str
    name: str
    chain: str
    totalErrors: int
    totalChecked: int
    statusStats: Optional[dict] = None
    totalReminders: int = 0

class DashboardSummaryResponse(BaseModel):
    success: bool
    overview: CalllogOverviewSummary
    chainStats: List[ChainCalllogStats]
    errorTypeStats: List[CalllogErrorTypeStats]
    ticketStatusStats: List[TicketStatusStats]
    topEmployees: List[EmployeeErrorRanking]
