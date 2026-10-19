from datetime import date
from pydantic import model_validator
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.import_service import ImportService
from app.repositories.import_repository import ImportRepository
from pydantic import BaseModel
from typing import Dict, Any

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

@router.post("/auth/start", response_model=AuthStatusResponse)
def auth_start(req: AuthStartRequest = None):
    session = FPTBrowserSession.get_instance()
    session._initial_probed = False
    creds = {"username": req.username, "password": req.password} if req else None
    import logging
    logging.getLogger(__name__).info(f"AUTH START USERNAME: {creds.get('username') if creds else None}")
    if creds and creds.get("username"):
        session.temp_creds = creds
    # Pass probe_only=False to ensure it's visible if needed
    status = session.start(probe_only=False)
    if status == "ERROR":
        raise HTTPException(status_code=500, detail="Browser failed to start")
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


@router.post("/sync", response_model=SyncResponse)
def sync_fpt_shop(req: SyncRequest, db: Session = Depends(get_db)):
    import logging
    logger = logging.getLogger(__name__)
    
    session = FPTBrowserSession.get_instance()
    status = session.get_status()
    if status != "AUTHENTICATED" or session.driver is None:
        if session.driver is None:
            status = session.start(headless=True)
        
    if status != "AUTHENTICATED" or session.driver is None:
        logger.error(f"[FPT_SYNC] Failed - FPT Shop browser session is not authenticated. Status: {status}")
        return SyncResponse(
            success=False,
            start_date=req.start_date,
            end_date=req.end_date,
            error_message="Phiên đăng nhập FPT Shop chưa được xác thực hoặc đã hết hạn. Vui lòng bấm Đăng nhập FPT."
        )

    logger.info(f"[FPT_SYNC] start={req.start_date.strftime("%Y-%m-%d")} end={req.end_date.strftime("%Y-%m-%d")}")
    logger.info("[FPT_SYNC] authenticated=true")
    logger.info("[FPT_SYNC] requesting GetDebtReportExcel")
    
    try:
        driver = session.driver
        body = f"Type=Gi%C3%A1m+s%C3%A1t+h%C3%ACnh+%E1%BA%A3nh+Camera&stepNo=-1&requestId=&Type=&Region=&sender=&timeStart={req.start_date.strftime('%d/%m/%Y')}&timeEnd={req.end_date.strftime('%d/%m/%Y')}&month_giuluong_37=&year_giuluong_37=&RegionId=&OfficeId=&TypeId=150"
        
        logger.info(f"[FPT_SYNC] current_url={driver.current_url}")
        driver.set_script_timeout(60)
        js_code = """
        var callback = arguments[arguments.length - 1];
        var bodyData = arguments[0];
        fetch("https://calllog.fptshop.com.vn/Report/GetDebtReportExcel", {
          "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "vi,en-US;q=0.9,en;q=0.8",
            "cache-control": "max-age=0",
            "content-type": "application/x-www-form-urlencoded",
            "upgrade-insecure-requests": "1"
          },
          "body": bodyData,
          "method": "POST",
          "mode": "cors",
          "credentials": "include"
        })
        .then(r => {
            if (!r.ok) {
                return r.text().then(t => {
                    callback({status: r.status, error: t});
                }).catch(() => {
                    callback({status: r.status, error: "HTTP Error " + r.status});
                });
            }
            var ct = r.headers.get("content-type");
            if (ct && ct.indexOf("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") === -1 && ct.indexOf("excel") === -1) {
                callback({status: 400, error: "Invalid Content-Type: " + ct});
                return null;
            }
            return r.blob().then(b => {
                var reader = new FileReader();
                reader.onload = function() { callback({status: 200, data: reader.result}); }
                reader.readAsDataURL(b);
            });
        })
        .catch(e => callback({status: 500, error: e.toString()}));
        """
        result = driver.execute_async_script(js_code, body)
        
        if result.get("status") != 200:
            status_code = result.get("status")
            if status_code in (401, 403):
                session.status = "LOGIN_PAGE"
                error_msg = "Phiên làm việc FPT Shop chưa được xác thực hoặc đã hết hạn (Mã 403). Vui lòng bấm 'Đăng nhập FPT' để đăng nhập lại."
            else:
                error_msg = f"Failed to download Excel. Status: {status_code}"
            logger.error(f"[FPT_SYNC] {error_msg}")
            return SyncResponse(
                success=False,
                start_date=req.start_date,
                end_date=req.end_date,
                error_message=error_msg
            )
            
        data_url = result.get("data")
        if not data_url or "," not in data_url:
            raise Exception("Invalid data received from browser")
            
        import base64
        base64_data = data_url.split(",")[1]
        file_bytes = base64.b64decode(base64_data)
        logger.info("[FPT_SYNC] xlsx received")
        
        # Now pass to existing ImportService
        import_service = ImportService(db)
        
        # Create a temp file name
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"BaoCaoChiTietThietBi_Camera-{timestamp}.xlsx"
        
        logger.info("[FPT_SYNC] IMPORT START")
        preview_res = import_service.preview(filename, file_bytes)
        if not preview_res.get("success"):
            logger.error(f"[FPT_SYNC] Import preview failed: {preview_res.get('error_message')}")
            return SyncResponse(
                success=False,
                start_date=req.start_date,
                end_date=req.end_date,
                error_message=preview_res.get('error_message', 'Preview failed')
            )
            
        commit_res = import_service.commit(preview_res["import_id"])
        if not commit_res.get("success"):
            logger.error(f"[FPT_SYNC] Import commit failed: {commit_res.get('error_message')}")
            return SyncResponse(
                success=False,
                start_date=req.start_date,
                end_date=req.end_date,
                error_message=commit_res.get('error_message', 'Commit failed')
            )
            
        # Reconcile: prune any tickets in this date range that were deleted/cancelled on FPT CallLog
        incoming_ids = [r.get("ticket_id") for r in preview_res.get("records", []) if r.get("ticket_id")]
        if incoming_ids:
            from app.models.ticket import Ticket
            from sqlalchemy import func
            deleted_q = db.query(Ticket).filter(
                Ticket.chain == "FPT_SHOP",
                func.date(Ticket.created_at) >= req.start_date,
                func.date(Ticket.created_at) <= req.end_date,
                ~Ticket.ticket_id.in_(incoming_ids)
            )
            pruned_count = deleted_q.delete(synchronize_session=False)
            if pruned_count > 0:
                db.commit()
                logger.info(f"[FPT_SYNC] Pruned {pruned_count} deleted/cancelled tickets")

        summary = commit_res.get("summary", {})
        logger.info(f"[FPT_SYNC] rows={summary.get('total', 0)}")
        logger.info(f"[FPT_SYNC] inserted={summary.get('new', 0)}")
        logger.info(f"[FPT_SYNC] updated={summary.get('updated', 0)}")
        logger.info(f"[FPT_SYNC] duplicates={summary.get('duplicate', 0)}")
        logger.info("[FPT_SYNC] complete")
        
        return SyncResponse(
            success=True,
            start_date=req.start_date,
            end_date=req.end_date,
            file_name=filename,
            total_rows=summary.get("total", 0),
            new_records=summary.get("new", 0),
            updated_records=summary.get("updated", 0),
            duplicate_records=summary.get("duplicate", 0),
            invalid_records=summary.get("invalid", 0)
        )
        
    except Exception as e:
        logger.error(f"[FPT_SYNC] Error: {str(e)}")
        return SyncResponse(
            success=False,
            start_date=req.start_date,
            end_date=req.end_date,
            error_message=str(e)
        )
    finally:
        if getattr(session, 'is_headless', False):
            session.stop()



