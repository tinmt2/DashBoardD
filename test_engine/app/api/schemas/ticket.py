from pydantic import BaseModel
from typing import Optional, List, Any, Dict

class TicketOutputFile(BaseModel):
    available: bool
    filename: Optional[str] = None

class TicketError(BaseModel):
    code: str
    message: str

class TicketLog(BaseModel):
    msg: str

class TicketJobState(BaseModel):
    success: bool
    status: str
    job_id: str
    message: Optional[str] = None
    progress: int
    total: int
    results: List[Any]
    logs: List[TicketLog]
    output_file: Optional[TicketOutputFile] = None
    error: Optional[TicketError] = None
