import re
import json
import logging
import unicodedata
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date
from typing import Optional, List, Dict, Any

from app.models.ticket import Ticket
from app.models.long_chau import LongChauTicketDetail
from app.schemas.ticket import CHAIN_LONG_CHAU
from app.schemas.long_chau_dashboard import (
    LongChauDashboardData,
    LongChauChainStats,
    LongChauErrorTypeStat,
    LongChauEmployeeStat,
    LongChauShopStat,
    LongChauRegionStat
)
from app.core.reminder import get_reminder_filter

class LongChauDashboardSummary:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> LongChauDashboardData:
        
        # Base query for Tickets
        query = self.db.query(Ticket).filter(Ticket.chain == CHAIN_LONG_CHAU)
        
        # Base query for Joins
        join_query = self.db.query(Ticket, LongChauTicketDetail).join(
            LongChauTicketDetail, Ticket.id == LongChauTicketDetail.ticket_record_id
        ).filter(Ticket.chain == CHAIN_LONG_CHAU)
        
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
        total_reminders = query.filter(Ticket.note.isnot(None), get_reminder_filter(Ticket.note)).count()

        # Employees (count distinct users case-insensitively)
        requesters = join_query.filter(
            LongChauTicketDetail.requester.isnot(None), 
            func.trim(LongChauTicketDetail.requester) != ''
        ).with_entities(LongChauTicketDetail.requester).all()
        total_employees = len(set(r[0].split('@')[0].strip().lower() for r in requesters if r[0]))

        error_requesters = join_query.filter(
            Ticket.error_status == "ERROR",
            LongChauTicketDetail.requester.isnot(None), 
            func.trim(LongChauTicketDetail.requester) != ''
        ).with_entities(LongChauTicketDetail.requester).all()
        employees_with_errors = len(set(r[0].split('@')[0].strip().lower() for r in error_requesters if r[0]))

        # Shops
        total_shops = query.filter(
            Ticket.shop_code.isnot(None), 
            func.trim(Ticket.shop_code) != ''
        ).with_entities(func.count(func.distinct(Ticket.shop_code))).scalar() or 0

        # Employee Error Ranking & Status Breakdown (Normalized case-insensitively)
        from collections import defaultdict
        emp_counts = defaultdict(int)
        emp_status_map = defaultdict(lambda: defaultdict(int))
        emp_reminders_map = defaultdict(int)
        emp_canonical_name = {}

        employee_tickets = join_query.filter(
            Ticket.error_status == "ERROR",
            LongChauTicketDetail.requester.isnot(None),
            func.trim(LongChauTicketDetail.requester) != ''
        ).with_entities(
            LongChauTicketDetail.requester,
            Ticket.ticket_status,
            Ticket.note
        ).all()

        for req, status, note in employee_tickets:
            raw_id = req.split('@')[0].strip() if '@' in req else req.strip()
            key = raw_id.lower()
            if not key:
                continue

            if key not in emp_canonical_name or (raw_id != raw_id.lower() and emp_canonical_name[key] == emp_canonical_name[key].lower()):
                emp_canonical_name[key] = raw_id

            emp_counts[key] += 1
            s_name = status if status else "Khác"
            emp_status_map[key][s_name] += 1

            if note and any(k in note.lower() for k in ["nhắc", "nhac", "reminder", "remind"]):
                emp_reminders_map[key] += 1

        employee_ranking = []
        for key, count in sorted(emp_counts.items(), key=lambda x: x[1], reverse=True):
            canon_name = emp_canonical_name[key]
            employee_ranking.append(LongChauEmployeeStat(
                employeeName=canon_name,
                errorCount=count,
                statusStats=dict(emp_status_map[key]),
                totalReminders=emp_reminders_map[key]
            ))

        # Error Type Ranking
        all_errors = join_query.filter(
            Ticket.error_status == "ERROR",
            Ticket.error_type.isnot(None)
        ).with_entities(
            Ticket.error_type,
            LongChauTicketDetail.requester
        ).all()
        
        error_type_counts = defaultdict(int)
        error_type_employees = defaultdict(lambda: defaultdict(int))
        
        for r in all_errors:
            etype = r.error_type
            error_type_counts[etype] += 1
            raw_emp = r.requester.split('@')[0].strip() if r.requester else "Unknown"
            emp_key = raw_emp.lower()
            canon_emp = emp_canonical_name.get(emp_key, raw_emp)
            error_type_employees[etype][canon_emp] += 1
            
        error_type_stats = []
        for etype, count in sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True):
            emps = [{"name": name, "count": c} for name, c in sorted(error_type_employees[etype].items(), key=lambda x: x[1], reverse=True)]
            error_type_stats.append(LongChauErrorTypeStat(errorType=etype, count=count, employees=emps))

        # Shop Error Ranking
        shop_results = query.filter(
            Ticket.error_status == "ERROR"
        ).with_entities(
            Ticket.shop_code, 
            Ticket.shop_name, 
            func.count(Ticket.id).label('count')
        ).group_by(Ticket.shop_code, Ticket.shop_name).order_by(func.count(Ticket.id).desc()).all()
        
        shop_ranking = [
            LongChauShopStat(shopCode=r.shop_code, shopName=r.shop_name, errorCount=r.count)
            for r in shop_results
        ]

        # Region Error Stats
        region_results = join_query.filter(
            Ticket.error_status == "ERROR"
        ).with_entities(
            LongChauTicketDetail.region,
            func.count(Ticket.id).label('count')
        ).group_by(LongChauTicketDetail.region).order_by(func.count(Ticket.id).desc()).all()
        
        region_ranking = [
            LongChauRegionStat(region=r.region, errorCount=r.count)
            for r in region_results
        ]

        chain_stats = LongChauChainStats(
            total=total_checked,
            errors=total_errors,
            errorRate=error_rate
        )

        return LongChauDashboardData(
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

