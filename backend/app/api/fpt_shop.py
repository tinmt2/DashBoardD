from datetime import date
from pydantic import model_validator
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.import_service import ImportService
from app.repositories.import_repository import ImportRepository
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter()

class CommitRequest(BaseModel):
    import_id: str

@router.post("/import/preview")
async def import_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    service = ImportService(db)
    result = service.preview(file.filename, content)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error_message"))
    return result

@router.post("/import/commit")
def import_commit(req: CommitRequest, db: Session = Depends(get_db)):
    service = ImportService(db)
    result = service.commit(req.import_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error_message"))
    return result

@router.get("/import/history")
def import_history(db: Session = Depends(get_db)):
    repo = ImportRepository(db)
    jobs = repo.get_all()
    history = []
    for j in jobs:
        history.append({
            "import_id": j.id,
            "filename": j.filename,
            "created_at": j.created_at,
            "status": j.status,
            "total_rows": j.total_rows,
            "valid_rows": j.valid_rows,
            "invalid_rows": j.invalid_rows,
            "new_count": j.new_rows,
            "duplicate_count": j.duplicate_rows,
            "error_message": j.error_message
        })
    return {"success": True, "history": history}

from app.services.dashboard.fpt_shop_summary import FPTShopSummaryService
from app.repositories.ticket_repository import SQLiteTicketRepository

@router.get("/data")
def get_dashboard_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = SQLiteTicketRepository(db)
    records, total = repo.get_all(skip=skip, limit=limit, chain="FPT_SHOP")
    return {
        "success": True,
        "data": [r.model_dump() for r in records],
        "total": total
    }

@router.get("/summary")
def get_dashboard_summary(from_date: str = Query(None), to_date: str = Query(None), db: Session = Depends(get_db)):
    repo = SQLiteTicketRepository(db)
    service = FPTShopSummaryService(repo)
    return service.get_summary(from_date=from_date, to_date=to_date)


from app.services.fpt_shop.browser_session import FPTBrowserSession

class AuthStatusResponse(BaseModel):
    authenticated: bool
    status: str

class AuthStartRequest(BaseModel):
    username: str = ""
    password: str = ""
    otp: str = ""

class OtpRequest(BaseModel):
    otp: str
    username: Optional[str] = ""
    password: Optional[str] = ""

@router.post("/auth/start", response_model=AuthStatusResponse)
def auth_start(req: AuthStartRequest = None):
    session = FPTBrowserSession.get_instance()
    session._initial_probed = False
    creds = {"username": req.username, "password": req.password, "otp": req.otp} if req else None
    import logging
    logging.getLogger(__name__).info(f"AUTH START USERNAME: {creds.get('username') if creds else None}")
    if creds and creds.get("username"):
        session.temp_creds = creds
        session._save_creds(creds)
    # Pass probe_only=False to ensure it's visible if needed
    status = session.start(probe_only=False)
    if status == "ERROR":
        raise HTTPException(status_code=500, detail="Browser failed to start")
        
    # If credentials were provided, give the browser up to 3 seconds to auto-submit and redirect
    if creds and creds.get("username") and creds.get("password"):
        import time
        for _ in range(6):
            time.sleep(0.5)
            status = session.get_status()
            if status in ("AUTHENTICATED", "LOGIN_FAILED", "OTP_REQUIRED"):
                break

    return AuthStatusResponse(
        authenticated=(status == "AUTHENTICATED"),
        status=status
    )

@router.post("/auth/otp", response_model=AuthStatusResponse)
def auth_otp(req: OtpRequest):
    session = FPTBrowserSession.get_instance()
    status = session.submit_otp(req.otp, username=req.username, password=req.password)
    return AuthStatusResponse(
        authenticated=(status == "AUTHENTICATED"),
        status=status
    )

@router.get("/auth/status", response_model=AuthStatusResponse)
def auth_status():
    session = FPTBrowserSession.get_instance()
    status = session.get_status()
    if status == "STOPPED" and not getattr(session, '_initial_probed', False):
        session._initial_probed = True
        status = session.start(probe_only=True)
    return AuthStatusResponse(
        authenticated=(status == "AUTHENTICATED"),
        status=status
    )


class SyncRequest(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode='after')
    def check_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        return self

class SyncResponse(BaseModel):
    success: bool
    source: str = "INTERNAL_WEB"
    start_date: date
    end_date: date
    file_name: str = ""
    total_rows: int = 0
    new_records: int = 0
    updated_records: int = 0
    duplicate_records: int = 0
    invalid_records: int = 0
    error_message: str = None


from app.services.fpt_shop.sync_db import sync_fpt_shop_data

@router.post("/sync", response_model=SyncResponse)
def sync_fpt_shop(req: SyncRequest, db: Session = Depends(get_db)):
    res = sync_fpt_shop_data(db, req.start_date, req.end_date)
    return SyncResponse(**res)



