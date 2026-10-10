from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.schemas.ticket import TicketRecord

class ImportSessionStatus(BaseModel):
    id: str
    filename: str
    created_at: datetime
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    new_rows: int = 0
    status: str # CREATED, PARSING, PREVIEW_READY, WAITING_CONFIRMATION, COMMITTING, COMPLETED, FAILED
    error_message: Optional[str] = None

class ImportPreviewResponse(BaseModel):
    import_id: str
    status: str
    mapping: List[Dict[str, Any]]
    validation: Dict[str, Any]
    preview: List[TicketRecord]
