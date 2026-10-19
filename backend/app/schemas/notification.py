from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChainSyncDetail(BaseModel):
    chain: str  # "FPT Shop", "Long Châu", "Vaccine"
    status: str  # "SUCCESS", "FAILED"
    new_records: int = 0  # Số lỗi cập nhật được thêm
    total_rows: int = 0
    duplicate_records: int = 0
    error_message: Optional[str] = None

class NotificationCreate(BaseModel):
    title: str
    status: str  # "SUCCESS", "FAILED", "PARTIAL"
    sync_type: str  # "SYNC_ALL", "FPT_SHOP", "LONG_CHAU", "VACCINE", "IMPORT_EXCEL"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_new_errors: int = 0
    total_scanned: int = 0
    total_duplicates: int = 0
    chain_details: Optional[List[ChainSyncDetail]] = []
    error_message: Optional[str] = None

class NotificationResponse(BaseModel):
    id: str
    title: str
    status: str
    sync_type: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_new_errors: int = 0
    total_scanned: int = 0
    total_duplicates: int = 0
    chain_details: List[ChainSyncDetail] = []
    error_message: Optional[str] = None
    is_read: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
