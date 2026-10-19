from app.repositories.ticket_repository import SQLiteTicketRepository
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    CalllogOverviewSummary,
    ChainCalllogStats,
    CalllogErrorTypeStats,
    EmployeeErrorRanking,
    TicketStatusStats
)
import hashlib
from typing import Optional

class FPTShopSummaryService:
    def __init__(self, repository: SQLiteTicketRepository):
        self.repository = repository

    def get_summary(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> DashboardSummaryResponse:
        data = self.repository.get_summary(chain="FPT_SHOP", from_date=from_date, to_date=to_date)

        total = data["total_checked"]
        errors = data["total_errors"]
        rate = round((errors / total) * 100, 2) if total > 0 else 0.0

        overview = CalllogOverviewSummary(
            totalErrors=errors,
            totalChecked=total,
            errorRate=rate,
            employeesWithErrors=data.get("employees_with_errors", 0),
            totalEmployees=data.get("total_employees", 0),
            totalReminders=data.get("total_reminders", 0)
        )

        fpt = data["chain_stats"].get("FPT_SHOP", {"total": 0, "errors": 0})
        fpt_total = fpt["total"]
        fpt_errors = fpt["errors"]
        fpt_rate = round((fpt_errors / fpt_total) * 100, 2) if fpt_total > 0 else 0.0

        chain_stats = [
            ChainCalllogStats(
                chain="FPT Shop",
                totalErrors=fpt_errors,
                totalChecked=fpt_total,
                errorRate=fpt_rate,
                color="blue" # Some default mapping
            )
        ]

        error_type_stats = []
        for e_type, e_count, emps in data["error_types"]:
            t_name = e_type if e_type else "Khác"
            emps.sort(key=lambda x: x["count"], reverse=True)
            error_type_stats.append(CalllogErrorTypeStats(
                type=t_name,
                count=e_count,
                employees=emps
            ))
            
        # Sort by count desc
        error_type_stats.sort(key=lambda x: x.count, reverse=True)

        ticket_status_stats = []
        for s_type, s_count in data["ticket_statuses"]:
            t_name = s_type if s_type else "Khác"
            ticket_status_stats.append(TicketStatusStats(status=t_name, count=s_count))
        ticket_status_stats.sort(key=lambda x: x.count, reverse=True)

        top_employees = []
        for emp_id, emp_name, emp_total, emp_errs in data["employee_stats"]:
            if emp_errs > 0:
                if not emp_id: emp_id = hashlib.md5(emp_name.encode('utf-8')).hexdigest()[:8]
                stats = data.get("employee_status_map", {}).get(emp_id, {})
                reminders = data.get("employee_reminders_map", {}).get(emp_id, 0)
                top_employees.append(EmployeeErrorRanking(
                    employeeId=emp_id,
                    name=emp_name,
                    chain="FPT Shop",
                    totalErrors=emp_errs,
                    totalChecked=emp_total,
                    statusStats=stats,
                    totalReminders=reminders
                ))
                
        top_employees.sort(key=lambda x: x.totalErrors, reverse=True)

        return DashboardSummaryResponse(
            success=True,
            overview=overview,
            chainStats=chain_stats,
            errorTypeStats=error_type_stats,
            ticketStatusStats=ticket_status_stats,
            topEmployees=top_employees[:10] # e.g. top 10
        )



