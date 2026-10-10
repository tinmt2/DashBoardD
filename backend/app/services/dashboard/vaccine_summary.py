import re
import json
import logging
import unicodedata
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date
from typing import Optional, List, Dict, Any

from app.models.ticket import Ticket
from app.models.vaccine import VaccineTicketDetail
from app.schemas.ticket import CHAIN_VACCINE
from app.schemas.vaccine_dashboard import (
    VaccineDashboardData,
    VaccineChainStats,
    VaccineErrorTypeStat,
    VaccineEmployeeStat,
    VaccineShopStat,
    VaccineRegionStat
)

class VaccineDashboardSummary:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> VaccineDashboardData:
        
        # Base query for Tickets
        query = self.db.query(Ticket).filter(Ticket.chain == CHAIN_VACCINE)
        
        # Base query for Joins
        join_query = self.db.query(Ticket, VaccineTicketDetail).join(
            VaccineTicketDetail, Ticket.id == VaccineTicketDetail.ticket_record_id
        ).filter(Ticket.chain == CHAIN_VACCINE)
        
        if from_date:
            query = query.filter(func.date(Ticket.created_at) >= from_date)
            join_query = join_query.filter(func.date(Ticket.created_at) >= from_date)
        if to_date:
            query = query.filter(func.date(Ticket.created_at) <= to_date)
            join_query = join_query.filter(func.date(Ticket.created_at) <= to_date)
            
        total_checked = query.count()
        total_errors = query.filter(Ticket.error_status == "ERROR").count()
        error_rate = (total_errors / total_checked * 100.0) if total_checked > 0 else 0.0

        # Global Ticket Status Stats
        ticket_statuses = query.with_entities(
            Ticket.ticket_status, 
            func.count(Ticket.id)
        ).group_by(Ticket.ticket_status).all()
        ticket_status_stats = [{"status": s if s else "Khác", "count": c} for s, c in ticket_statuses]

        # Global Total Reminders (from note)
        total_reminders = query.filter(Ticket.note.isnot(None), func.trim(Ticket.note) != '').count()

        # Employees
        total_employees = join_query.filter(
            VaccineTicketDetail.requester.isnot(None), 
            func.trim(VaccineTicketDetail.requester) != ''
        ).with_entities(func.count(func.distinct(VaccineTicketDetail.requester))).scalar() or 0

        employees_with_errors = join_query.filter(
            Ticket.error_status == "ERROR",
            VaccineTicketDetail.requester.isnot(None), 
            func.trim(VaccineTicketDetail.requester) != ''
        ).with_entities(func.count(func.distinct(VaccineTicketDetail.requester))).scalar() or 0

        # Shops
        total_shops = query.filter(
            Ticket.shop_code.isnot(None), 
            func.trim(Ticket.shop_code) != ''
        ).with_entities(func.count(func.distinct(Ticket.shop_code))).scalar() or 0

        # Error Type Ranking
        all_errors = join_query.filter(
            Ticket.error_status == "ERROR",
            Ticket.error_type.isnot(None)
        ).with_entities(
            Ticket.error_type,
            VaccineTicketDetail.requester
        ).all()
        
        from collections import defaultdict
        error_type_counts = defaultdict(int)
        error_type_employees = defaultdict(lambda: defaultdict(int))
        
        for r in all_errors:
            etype = r.error_type
            error_type_counts[etype] += 1
            emp = r.requester.split('@')[0] if r.requester else "Unknown"
            error_type_employees[etype][emp] += 1
            
        error_type_stats = []
        for etype, count in sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True):
            emps = [{"name": name, "count": c} for name, c in sorted(error_type_employees[etype].items(), key=lambda x: x[1], reverse=True)]
            error_type_stats.append(VaccineErrorTypeStat(errorType=etype, count=count, employees=emps))

        # Employee Error Ranking (group by requester, strip @fpt.com)
        employee_results = join_query.filter(
            Ticket.error_status == "ERROR",
            VaccineTicketDetail.requester.isnot(None),
            func.trim(VaccineTicketDetail.requester) != ''
        ).with_entities(
            VaccineTicketDetail.requester.label("requester"), 
            func.count(Ticket.id).label('count')
        ).group_by(VaccineTicketDetail.requester).order_by(func.count(Ticket.id).desc()).all()
        
        # Employee Status Stats
        emp_status_query = join_query.filter(
            Ticket.error_status == "ERROR",
            VaccineTicketDetail.requester.isnot(None),
            func.trim(VaccineTicketDetail.requester) != ''
        ).with_entities(
            VaccineTicketDetail.requester,
            Ticket.ticket_status,
            func.count(Ticket.id)
        ).group_by(VaccineTicketDetail.requester, Ticket.ticket_status).all()

        emp_status_map = {}
        for req, status, count in emp_status_query:
            if not req: continue
            name = req.split('@')[0] if '@' in req else req
            if name not in emp_status_map:
                emp_status_map[name] = {}
            s_name = status if status else "Khác"
            emp_status_map[name][s_name] = count

        # Employee Reminders
        emp_reminders_query = join_query.filter(
            VaccineTicketDetail.requester.isnot(None),
            func.trim(VaccineTicketDetail.requester) != '',
            Ticket.note.isnot(None), func.trim(Ticket.note) != ''
        ).with_entities(
            VaccineTicketDetail.requester,
            func.count(Ticket.id)
        ).group_by(VaccineTicketDetail.requester).all()

        emp_reminders_map = {}
        for req, count in emp_reminders_query:
            if not req: continue
            name = req.split('@')[0] if '@' in req else req
            emp_reminders_map[name] = emp_reminders_map.get(name, 0) + count

        employee_ranking = []
        for r in employee_results:
            name = r.requester.split('@')[0] if '@' in r.requester else r.requester
            employee_ranking.append(VaccineEmployeeStat(
                employeeName=name, 
                errorCount=r.count,
                statusStats=emp_status_map.get(name, {}),
                totalReminders=emp_reminders_map.get(name, 0)
            ))

        # Shop Error Ranking
        shop_results = query.filter(
            Ticket.error_status == "ERROR"
        ).with_entities(
            Ticket.shop_code, 
            Ticket.shop_name, 
            func.count(Ticket.id).label('count')
        ).group_by(Ticket.shop_code, Ticket.shop_name).order_by(func.count(Ticket.id).desc()).all()
        
        shop_ranking = [
            VaccineShopStat(shopCode=r.shop_code, shopName=r.shop_name, errorCount=r.count)
            for r in shop_results
        ]

        # Region Error Stats
        region_results = join_query.filter(
            Ticket.error_status == "ERROR"
        ).with_entities(
            VaccineTicketDetail.region,
            func.count(Ticket.id).label('count')
        ).group_by(VaccineTicketDetail.region).order_by(func.count(Ticket.id).desc()).all()
        
        region_ranking = [
            VaccineRegionStat(region=r.region, errorCount=r.count)
            for r in region_results
        ]

        chain_stats = VaccineChainStats(
            total=total_checked,
            errors=total_errors,
            errorRate=error_rate
        )

        return VaccineDashboardData(
            totalChecked=total_checked,
            totalErrors=total_errors,
            errorRate=error_rate,
            totalEmployees=total_employees,
            employeesWithErrors=employees_with_errors,
            totalShops=total_shops,
            totalReminders=total_reminders,
            chainStats=chain_stats,
            errorTypeStats=error_type_stats,
            employeeErrorRanking=employee_ranking,
            shopErrorRanking=shop_ranking,
            regionErrorStats=region_ranking,
            ticketStatusStats=ticket_status_stats
        )

