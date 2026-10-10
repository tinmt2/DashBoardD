from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

# Chain identifiers stored in TicketRecord.chain / tickets.chain.
# "FPT_SHOP" is the original FPT Shop pipeline value (unchanged).
# "LongChâu" is set exclusively by the LongChâu import pipeline (backend-enforced).
CHAIN_FPT_SHOP = "FPT_SHOP"
CHAIN_LONG_CHAU = "LongChâu"
CHAIN_VACCINE = "Vaccine"

class TicketRecord(BaseModel):
    id: str
    chain: Literal["FPT_SHOP", "LongChâu", "Vaccine"] = "FPT_SHOP"
    ticket_id: str
    employee_id: Optional[str] = None
    # Nullable so chains whose reports may not name a violating employee
    # (e.g. LongChâu "NHÂN VIÊN VI PHẠM" empty) are stored as null instead of
    # a guessed person. FPT Shop still requires it via its own RecordValidator.
    employee_name: Optional[str] = None
    shop_code: Optional[str] = None
    shop_name: Optional[str] = None
    created_at: Optional[datetime] = None
    checked_at: Optional[datetime] = None
    error_status: Literal["ERROR", "PASS", "PENDING"]
    error_type: Optional[str] = None
    error_reason: Optional[str] = None
    ticket_status: Optional[str] = None
    note: Optional[str] = None
    source: Literal["EXCEL", "INTERNAL_WEB"]
    imported_at: datetime
