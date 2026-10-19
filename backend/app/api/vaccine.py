"""
Vaccine Excel import endpoints and API Sync.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.vaccine.service import VaccineImportService

router = APIRouter()

MAX_UPLOAD_BYTES = 25 * 1024 * 1024

class VaccineCommitRequest(BaseModel):
    import_id: str = Field(validation_alias=AliasChoices("import_id", "importId"))

@router.post("/import/preview")
async def vaccine_import_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File qua lon")
    if not content:
        raise HTTPException(status_code=400, detail="File rong")
    result = VaccineImportService(db).preview(file.filename or "upload", content)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error_message") or result.get("error"))
    return result

@router.post("/import/commit")
def vaccine_import_commit(req: VaccineCommitRequest, db: Session = Depends(get_db)):
    result = VaccineImportService(db).commit(req.import_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error_message") or result.get("error"))
    return result

@router.get("/import/history")
def vaccine_import_history(limit: int = 100, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    return {"success": True, "history": VaccineImportService(db).history(limit)}

from app.services.vaccine.login.browser_session import VaccineBrowserSession
from app.services.vaccine.api.sync_db import sync_vaccine_data

class SyncRequest(BaseModel):
    start_date: str
    end_date: str

from typing import Optional
class AuthStartReq(BaseModel):
    username: str = ""
    password: str = ""
    otp: str = ""

class OtpRequest(BaseModel):
    otp: str

@router.post("/auth/start")
def vaccine_auth_start(req: Optional[AuthStartReq] = None):
    session = VaccineBrowserSession.get_instance()
    if req:
        session.temp_creds = req.dict()
    status = session.start()
    return {"authenticated": status == "AUTHENTICATED", "status": status}

@router.post("/auth/otp")
def vaccine_auth_otp(req: OtpRequest):
    session = VaccineBrowserSession.get_instance()
    status = session.submit_otp(req.otp)
    return {"authenticated": status == "AUTHENTICATED", "status": status}

@router.get("/auth/status")
def vaccine_auth_status():
    session = VaccineBrowserSession.get_instance()
    status = session.get_status()
    if status == "STOPPED" and not getattr(session, '_initial_probed', False):
        session._initial_probed = True
        status = session.start(probe_only=True)
    return {"authenticated": status == "AUTHENTICATED", "status": status}

@router.post("/sync")
def vaccine_sync(req: SyncRequest, db: Session = Depends(get_db)):
    session = VaccineBrowserSession.get_instance()
    status = session.get_status()
    has_cached = bool(getattr(session, "cached_cookies", None) and any(k in session.cached_cookies for k in ['budibase:auth', 'bb-auth']))
    if not has_cached and (status == "STOPPED" or session.driver is None):
        status = session.start(probe_only=True)
    if status != "AUTHENTICATED":
        raise HTTPException(status_code=401, detail="Vui lòng đăng nhập Vaccine trước khi đồng bộ.")
    
    cookies = session.get_auth_cookies()
    if not cookies:
        raise HTTPException(status_code=401, detail="Không thể lấy cookie xác thực Vaccine")
        
    headers = session.get_auth_headers()
    res = sync_vaccine_data(db, cookies, headers, req.start_date, req.end_date)
    if not res.get("success"):
        msg = str(res.get("message"))
        if "403" in msg or "401" in msg or "Forbidden" in msg or "Unauthorized" in msg:
            session.cached_cookies = None
            session.cached_headers = None
            session.status = "STOPPED"
            session._needs_storage_clear = True
            session.clear_driver()
            raise HTTPException(status_code=401, detail="Phiên đăng nhập Vaccine đã hết hạn hoặc chưa đăng nhập, vui lòng bấm Đăng nhập Vaccine để tiếp tục.")
        raise HTTPException(status_code=500, detail=msg)
        
    return {
        "success": True,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "total_rows": res.get("total", res.get("inserted", 0) + res.get("duplicates", 0)),
        "new_records": res.get("inserted", 0),
        "duplicate_records": res.get("duplicates", 0),
        "error_message": None
    }
