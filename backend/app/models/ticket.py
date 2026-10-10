from sqlalchemy import Column, String, DateTime, Enum, Integer
from app.core.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, index=True)
    chain = Column(String, default="FPT_SHOP", index=True)
    ticket_id = Column(String, index=True)
    employee_id = Column(String, index=True, nullable=True)
    employee_name = Column(String)
    shop_code = Column(String, nullable=True)
    shop_name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    checked_at = Column(DateTime, nullable=True)
    error_status = Column(String)
    error_type = Column(String, nullable=True)
    error_reason = Column(String, nullable=True)
    ticket_status = Column(String, nullable=True)
    note = Column(String, nullable=True)
    source = Column(String)
    imported_at = Column(DateTime)
