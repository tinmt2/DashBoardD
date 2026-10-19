from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import Ticket
from app.schemas.ticket import TicketRecord
from app.repositories.repository_interface import TicketRepository

class SQLiteTicketRepository(TicketRepository):
    def __init__(self, db: Session):
        self.db = db

    def insert_many(self, records: List[TicketRecord]) -> None:
        if not records:
            return
        
        db_records = []
        for r in records:
            db_record = Ticket(**r.model_dump())
            db_records.append(db_record)
            
        self.db.bulk_save_objects(db_records)
        self.db.flush()

    def get_all(self, skip: int = 0, limit: int = 100, chain: Optional[str] = None) -> Tuple[List[TicketRecord], int]:
        base = self.db.query(Ticket)
        if chain is not None:
            base = base.filter(Ticket.chain == chain)
        total = base.count()
        tickets = base.offset(skip).limit(limit).all()
        return [TicketRecord.model_validate(t, from_attributes=True) for t in tickets], total

    def find_by_ticket_id(self, ticket_id: str) -> Optional[TicketRecord]:
        t = self.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if t:
            return TicketRecord.model_validate(t, from_attributes=True)
        return None

    def get_summary(self, chain: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict[str, Any]:
        self._from_date = from_date
        self._to_date = to_date
        # Optional chain scope: FPT Shop summary passes chain="FPT_SHOP" so data
        # from other chains (e.g. LongChÃ¢u imports) never changes FPT KPIs.
        def scoped(query):
            q = query.filter(Ticket.chain == chain) if chain is not None else query
            if getattr(self, '_from_date', None):
                q = q.filter(func.date(Ticket.created_at) >= self._from_date)
            if getattr(self, '_to_date', None):
                q = q.filter(func.date(Ticket.created_at) <= self._to_date)
            return q

        # 1. totalChecked, totalErrors
        total_checked = scoped(self.db.query(Ticket)).count()
        total_errors = scoped(self.db.query(Ticket)).filter(Ticket.error_status == "ERROR").count()
        
        # 2. totalEmployees, employeesWithErrors
        # SQLite distinct count: 
        total_employees = scoped(self.db.query(func.count(func.distinct(Ticket.employee_id)))).scalar() or 0
        employees_with_errors = scoped(self.db.query(func.count(func.distinct(Ticket.employee_id)))).filter(Ticket.error_status == "ERROR").scalar() or 0
        
        # 3. Chain Stats (Only FPT_SHOP for now)
        fpt_total = self.db.query(Ticket).filter(Ticket.chain == "FPT_SHOP").count()
        fpt_errors = self.db.query(Ticket).filter(Ticket.chain == "FPT_SHOP", Ticket.error_status == "ERROR").count()
        
        # 4. Error Type Stats
        error_types_raw = scoped(self.db.query(Ticket.error_type, Ticket.employee_name)).filter(Ticket.error_status == "ERROR").all()
        from collections import defaultdict
        et_counts = defaultdict(int)
        et_emps = defaultdict(lambda: defaultdict(int))
        for etype, ename in error_types_raw:
            if not etype: continue
            et_counts[etype] += 1
            if ename: et_emps[etype][ename] += 1
            
        error_types = []
        for etype, count in et_counts.items():
            emps = [{"name": n, "count": c} for n, c in et_emps[etype].items()]
            error_types.append((etype, count, emps))
        
        # 4.5 Ticket Status Stats
        ticket_statuses = scoped(self.db.query(Ticket.ticket_status, func.count(Ticket.id))).group_by(Ticket.ticket_status).all()
        
        # 5. Top Employees
        from sqlalchemy import case
        emp_stats = scoped(self.db.query(
            Ticket.employee_id,
            Ticket.employee_name,
            func.count(Ticket.id).label('total_checked'),
            func.sum(case((Ticket.error_status == "ERROR", 1), else_=0)).label('total_errors')
        )).group_by(Ticket.employee_id, Ticket.employee_name).all()

        emp_status_query = scoped(self.db.query(
            Ticket.employee_id,
            Ticket.ticket_status,
            func.count(Ticket.id).label('count')
        )).filter(Ticket.error_status == "ERROR").group_by(Ticket.employee_id, Ticket.ticket_status).all()

        emp_status_map = {}
        for emp_id, status, count in emp_status_query:
            if not emp_id: continue
            if emp_id not in emp_status_map:
                emp_status_map[emp_id] = {}
            s_name = status if status else "Khác"
            emp_status_map[emp_id][s_name] = count

        from app.core.reminder import get_reminder_filter
        reminder_condition = get_reminder_filter(Ticket.note)
        total_reminders = scoped(self.db.query(func.count(Ticket.id))).filter(Ticket.note.isnot(None), reminder_condition).scalar() or 0
        emp_reminders_query = scoped(self.db.query(Ticket.employee_id, func.count(Ticket.id))).filter(Ticket.note.isnot(None), reminder_condition).group_by(Ticket.employee_id).all()
        emp_reminders_map = {emp_id: count for emp_id, count in emp_reminders_query if emp_id}

        return {
            "total_checked": total_checked,
            "total_errors": total_errors,
            "total_employees": total_employees,
            "employees_with_errors": employees_with_errors,
            "total_reminders": total_reminders,
            "chain_stats": {
                "FPT_SHOP": {
                    "total": fpt_total,
                    "errors": fpt_errors
                }
            },
            "error_types": error_types,
            "ticket_statuses": ticket_statuses,
            "employee_stats": emp_stats,
            "employee_status_map": emp_status_map,
            "employee_reminders_map": emp_reminders_map
        }




