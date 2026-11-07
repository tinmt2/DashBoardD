from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from app.core.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, index=True)  # Mail (e.g. "VienND2")
    inside_code = Column(String, nullable=True, index=True)  # Mã Inside (e.g. "51765")
    name = Column(String, nullable=False, index=True)
    chain = Column(String, nullable=False, default="FPT Shop", index=True)
    position = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Active", index=True)
    start_date = Column(String, nullable=True)
    total_errors = Column(Integer, default=0)
    total_checked = Column(Integer, default=0)
    last_activity = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class EmployeeTransferHistory(Base):
    __tablename__ = "employee_transfer_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, nullable=False, index=True)
    from_chain = Column(String, nullable=False)
    to_chain = Column(String, nullable=False)
    transferred_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    transferred_by = Column(String, nullable=True)

class MonthlyScheduleLink(Base):
    __tablename__ = "monthly_schedule_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(String, unique=True, index=True, nullable=False)  # e.g. "2026-11"
    title = Column(String, nullable=True)  # e.g. "Lịch làm việc Tháng 11/2026"
    file_name = Column(String, nullable=True)  # e.g. "1. LLV T11 2026.xlsx"
    sharepoint_url = Column(String, nullable=False)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class EmployeeShift(Base):
    __tablename__ = "employee_shifts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(String, index=True, nullable=False)  # "2026-11"
    employee_id = Column(String, index=True, nullable=False)  # "AnNT50", "LuanNV8"
    employee_code = Column(String, nullable=True)  # "50407", "32690"
    employee_name = Column(String, nullable=True)  # "Nguyễn Tấn An"
    chain = Column(String, default="FPT Shop", index=True)  # "FPT Shop", "Long Châu", "Vaccine"
    date = Column(String, index=True, nullable=False)  # "2026-11-23" (YYYY-MM-DD)
    shift_type = Column(String, nullable=False)  # "Ca Sáng", "Ca Chiều", "Trực đêm", "Sáng + đêm", "OFF", etc.
    day_of_week = Column(String, nullable=True)  # "Thứ 2", "Thứ 3"...
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
