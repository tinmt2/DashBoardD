"""
LongChâu Excel import endpoints (minimal surface for this phase).

    POST /api/long-chau/import/preview   multipart file=<Excel>
    POST /api/long-chau/import/commit    {"import_id": "..."} (or "importId")
    GET  /api/long-chau/import/history

``chain`` is never accepted from the client; the pipeline always sets "LongChâu".
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.long_chau.service import LongChauImportService

router = APIRouter()

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


class LongChauCommitRequest(BaseModel):
    import_id: str = Field(validation_alias=AliasChoices("import_id", "importId"))


@router.post("/import/preview")
async def long_chau_import_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File quá lớn (tối đa 25 MB).")
    if not content:
        raise HTTPException(status_code=400, detail="File rỗng.")

    result = LongChauImportService(db).preview(file.filename or "upload", content)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error_message"))
    return result


@router.post("/import/commit")
def long_chau_import_commit(req: LongChauCommitRequest, db: Session = Depends(get_db)):
    result = LongChauImportService(db).commit(req.import_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error_message"))
    return result


@router.get("/import/history")
def long_chau_import_history(limit: int = 100, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    return {"success": True, "history": LongChauImportService(db).history(limit)}

from typing import Optional
from app.services.long_chau.login.browser_session import LongChauBrowserSession
from app.services.long_chau.api.client import LongChauApiClient
from app.services.long_chau.api.sync_db import save_long_chau_api_records
from pydantic import BaseModel

class AuthStartReq(BaseModel):
    username: str = ""
    password: str = ""
    otp: str = ""

class OtpRequest(BaseModel):
    otp: str

class SyncRequest(BaseModel):
    start_date: str
    end_date: str

@router.post("/auth/start")
def long_chau_auth_start(req: Optional[AuthStartReq] = None):
    session = LongChauBrowserSession.get_instance()
    if req:
        session.temp_creds = req.dict()
    status = session.start()
    return {"authenticated": status == "AUTHENTICATED", "status": status}

@router.post("/auth/otp")
def long_chau_auth_otp(req: OtpRequest):
    session = LongChauBrowserSession.get_instance()
    status = session.submit_otp(req.otp)
    return {"authenticated": status == "AUTHENTICATED", "status": status}

@router.get("/auth/status")
def long_chau_auth_status():
    session = LongChauBrowserSession.get_instance()
    status = session.get_status()
    if status == "STOPPED" and not getattr(session, '_initial_probed', False):
        session._initial_probed = True
        status = session.start(probe_only=True)
    return {"authenticated": status == "AUTHENTICATED", "status": status}

@router.post("/sync")
def long_chau_sync(req: SyncRequest, db: Session = Depends(get_db)):
    session = LongChauBrowserSession.get_instance()
    status = session.get_status()
    # Check if we have cached cookies first with budibase:auth or bb-auth
    has_cached = bool(getattr(session, "cached_cookies", None) and any(k in session.cached_cookies for k in ['budibase:auth', 'bb-auth']))
    if not has_cached and (status == "STOPPED" or session.driver is None):
        status = session.start(probe_only=True)
    if status != "AUTHENTICATED":
        raise HTTPException(status_code=401, detail="Vui lòng đăng nhập Long Châu trước khi đồng bộ.")
    
    cookies = session.get_auth_cookies()
    if not cookies:
        raise HTTPException(status_code=401, detail="Không lấy được Cookie đăng nhập Long Châu.")
        
    client = LongChauApiClient(cookies, headers=session.get_auth_headers() if hasattr(session, 'get_auth_headers') else None)
    try:
        # Fetch data from Budibase API
        records = client.get_full_report(req.start_date, req.end_date)
        # Process and save
        inserted, duplicates = save_long_chau_api_records(db, records)
        return {
            "success": True,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "total_rows": len(records),
            "new_records": inserted,
            "duplicate_records": duplicates,
            "error_message": None
        }
    except Exception as e:
        msg = str(e)
        if "403" in msg or "401" in msg or "not authenticated" in msg.lower() or "Forbidden" in msg or "Unauthorized" in msg:
            session.cached_cookies = None
            session.cached_headers = None
            session.status = "STOPPED"
            session._needs_storage_clear = True
            session.clear_driver()
            raise HTTPException(status_code=401, detail="Phiên đăng nhập Long Châu đã hết hạn, vui lòng bấm Đăng nhập Long Châu để tiếp tục.")
        raise HTTPException(status_code=500, detail=str(e))
