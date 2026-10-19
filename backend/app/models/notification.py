from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from app.core.database import Base

class SyncNotification(Base):
    __tablename__ = "sync_notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)  # "SUCCESS", "FAILED", "PARTIAL"
    sync_type = Column(String, nullable=False)  # "SYNC_ALL", "FPT_SHOP", "LONG_CHAU", "VACCINE", "IMPORT_EXCEL"
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    total_new_errors = Column(Integer, default=0)
    total_scanned = Column(Integer, default=0)
    total_duplicates = Column(Integer, default=0)
    chain_details = Column(Text, nullable=True)  # JSON-encoded array of ChainSyncDetail
    error_message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
