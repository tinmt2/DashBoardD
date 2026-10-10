from sqlalchemy import Column, String, DateTime, Integer, Text
from app.core.database import Base

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    created_at = Column(DateTime)
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    new_rows = Column(Integer, default=0)
    status = Column(String)
    error_message = Column(String, nullable=True)
    preview_data = Column(Text, nullable=True)
