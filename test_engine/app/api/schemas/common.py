from pydantic import BaseModel
from typing import Optional, Any

class ApiResponse(BaseModel):
    success: bool
    status: str
    service: Optional[str] = None
    data: Optional[Any] = None
    message: Optional[str] = None
