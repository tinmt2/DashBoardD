from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from app.core.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, index=True)
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
