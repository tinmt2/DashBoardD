import os
import json
import time
import hashlib
import psutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.models.ticket import Ticket
from app.models.notification import SyncNotification
from app.models.import_job import ImportJob
from app.services.fpt_shop.browser_session import FPTBrowserSession
from app.services.long_chau.login.browser_session import LongChauBrowserSession
from app.services.vaccine.login.browser_session import VaccineBrowserSession

router = APIRouter()

from app.core.auth import (
    get_admin_config as _get_config,
    save_admin_config as _save_config,
    verify_admin_token,
    revoke_admin_token
)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "admin_config.json")
START_TIME = time.time()

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class TotpConfigRequest(BaseModel):
    secret: str

class TestTotpRequest(BaseModel):
    secret: Optional[str] = None

@router.post("/login")
def admin_login(req: LoginRequest):
    cfg = _get_config()
    input_hash = _hash_pw(req.password)
    
    if req.username != cfg.get("admin_username", "admin") or input_hash != cfg.get("admin_password_hash"):
        raise HTTPException(status_code=401, detail="Tài khoản hoặc mật khẩu Admin không chính xác!")
    
    token = hashlib.sha256(f"admin-{time.time()}-{req.password}".encode()).hexdigest()[:32]
    tokens = cfg.get("active_tokens", [])
    tokens.append({"token": token, "created_at": time.time()})
    # Keep last 10 tokens
    cfg["active_tokens"] = tokens[-10:]
    _save_config(cfg)
    
    return {
        "success": True,
        "token": token,
        "username": req.username,
        "message": "Đăng nhập Admin thành công!"
    }

@router.post("/verify")
def verify_token(authorization: Optional[str] = Header(None)):
    verify_admin_token(authorization)
    cfg = _get_config()
    return {"valid": True, "username": cfg.get("admin_username", "admin")}

@router.post("/logout")
def admin_logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "").strip()
        revoke_admin_token(token)
    return {"success": True, "message": "Đã đăng xuất phiên làm việc!"}

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, authorization: Optional[str] = Header(None)):
    verify_admin_token(authorization)
    cfg = _get_config()
    
    if _hash_pw(req.old_password) != cfg.get("admin_password_hash"):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng!")
    
    if len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 4 ký tự!")
        
    cfg["admin_password_hash"] = _hash_pw(req.new_password)
    _save_config(cfg)
    return {"success": True, "message": "Đổi mật khẩu Admin thành công!"}

@router.get("/totp-config")
def get_totp_config(authorization: Optional[str] = Header(None)):
    verify_admin_token(authorization)
    cfg = _get_config()
    
    secret = (cfg.get("totp_secret") or "").strip()
    from app.core.totp import generate_totp
    current_code = generate_totp(secret) if secret else None
    
    # Mask secret if returning (e.g. show first 4 and last 4)
    masked_secret = ""
    if secret:
        if len(secret) > 8:
            masked_secret = secret[:4] + "*" * (len(secret) - 8) + secret[-4:]
        else:
            masked_secret = "********"
            
    return {
        "has_secret": bool(secret),
        "masked_secret": masked_secret,
        "raw_secret": secret,
        "current_code": current_code
    }

@router.post("/totp-config")
def save_totp_config(req: TotpConfigRequest, authorization: Optional[str] = Header(None)):
    verify_admin_token(authorization)
    cfg = _get_config()
    
    from app.core.totp import extract_secret_from_input, generate_totp
    raw = req.secret.strip()
    secret = ""
    if raw:
        extracted = extract_secret_from_input(raw)
        if not extracted:
            raise HTTPException(status_code=400, detail="Không thể nhận diện Secret Key! Vui lòng kiểm tra lại chuỗi hoặc link xuất Authenticator.")
        secret = extracted
    
    cfg["totp_secret"] = secret
    _save_config(cfg)
    
    code = generate_totp(secret) if secret else None
    return {
        "success": True, 
        "has_secret": bool(secret),
        "secret": secret,
        "current_code": code,
        "message": "Đã trích xuất và lưu Secret Key thành công!" if secret else "Đã xóa Secret Key!"
    }

@router.post("/totp-config/test")
def test_totp_config(req: TestTotpRequest, authorization: Optional[str] = Header(None)):
    verify_admin_token(authorization)
    cfg = _get_config()
    
    secret = (req.secret or cfg.get("totp_secret") or "").strip().replace(" ", "").upper()
    if not secret:
        raise HTTPException(status_code=400, detail="Chưa có Secret Key để kiểm tra!")
        
    from app.core.totp import generate_totp
    code = generate_totp(secret)
    if not code:
        raise HTTPException(status_code=400, detail="Secret Key không đúng định dạng Base32!")
        
    return {
        "success": True,
        "code": code,
        "message": f"Mã TOTP 6 số hiện tại là: {code}"
    }

@router.get("/overview")
def admin_overview(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    verify_admin_token(authorization)
    # 1. Server & System Metrics
    uptime_sec = int(time.time() - START_TIME)
    hours, rem = divmod(uptime_sec, 3600)
    mins, secs = divmod(rem, 60)
    uptime_str = f"{hours}h {mins}m {secs}s"
    
    vmem = psutil.virtual_memory()
    system_metrics = {
        "status": "ONLINE",
        "port": 8000,
        "uptime_seconds": uptime_sec,
        "uptime_str": uptime_str,
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "ram_percent": vmem.percent,
        "ram_used_gb": round(vmem.used / (1024**3), 2),
        "ram_total_gb": round(vmem.total / (1024**3), 2),
    }
    
    # 2. Database Metrics
    db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "opsmonitor.db"))
    db_size_mb = 0.0
    if os.path.exists(db_file):
        db_size_mb = round(os.path.getsize(db_file) / (1024 * 1024), 2)
        
    total_tickets = db.query(Ticket).count()
    fpt_count = db.query(Ticket).filter(Ticket.chain == "FPT Shop").count()
    lc_count = db.query(Ticket).filter(Ticket.chain == "Long Châu").count()
    vac_count = db.query(Ticket).filter(Ticket.chain == "Vaccine").count()
    notif_count = db.query(SyncNotification).count()
    
    database_metrics = {
        "db_size_mb": db_size_mb,
        "total_tickets": total_tickets,
        "fpt_tickets": fpt_count,
        "long_chau_tickets": lc_count,
        "vaccine_tickets": vac_count,
        "notifications_count": notif_count
    }
    
    # 3. Chains Session Status
    def safe_status(cls):
        try:
            inst = cls.get_instance()
            st = inst.get_status()
            return {"status": st, "authenticated": st == "AUTHENTICATED"}
        except Exception as e:
            return {"status": "ERROR", "authenticated": False, "error": str(e)}

    chains_status = {
        "fpt_shop": safe_status(FPTBrowserSession),
        "long_chau": safe_status(LongChauBrowserSession),
        "vaccine": safe_status(VaccineBrowserSession)
    }
    
    # 4. Recent Notifications
    recent_notifs = []
    try:
        notifs = db.query(SyncNotification).order_by(SyncNotification.created_at.desc()).limit(10).all()
        for n in notifs:
            created_dt = n.created_at
            if created_dt and created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            recent_notifs.append({
                "id": n.id,
                "chain": getattr(n, "chain", None) or n.sync_type,
                "title": n.title,
                "message": getattr(n, "message", None) or n.error_message or "",
                "status": n.status,
                "created_at": created_dt.isoformat() if created_dt else None
            })
    except Exception:
        pass
        
    # 5. Recent Import Jobs
    recent_jobs = []
    try:
        jobs = db.query(ImportJob).order_by(ImportJob.created_at.desc()).limit(5).all()
        for j in jobs:
            recent_jobs.append({
                "id": j.id,
                "filename": j.filename,
                "status": j.status,
                "total_rows": j.total_rows,
                "created_at": j.created_at.isoformat() if j.created_at else None
            })
    except Exception:
        pass

    return {
        "system": system_metrics,
        "database": database_metrics,
        "chains": chains_status,
        "recent_notifications": recent_notifs,
        "recent_jobs": recent_jobs,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }

# ==========================================
# 6. LOGS & LIVE SYNC DIAGNOSTICS FOR ADMIN
# ==========================================
from fastapi import Query
from app.core.logging import get_recent_logs, clear_memory_logs

@router.get("/logs")
def get_admin_logs(
    lines: int = Query(200, ge=1, le=2000),
    level: Optional[str] = Query("ALL"),
    search: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    verify_admin_token(authorization)
    logs = get_recent_logs(lines=lines, level=level, search=search)
    return {
        "success": True,
        "total": len(logs),
        "logs": logs
    }

@router.delete("/logs")
def clear_admin_logs(authorization: Optional[str] = Header(None)):
    verify_admin_token(authorization)
    clear_memory_logs()
    return {"success": True, "message": "Đã làm trống toàn bộ log trong bộ nhớ!"}

@router.post("/test-sync/fpt")
def test_sync_fpt_admin(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    verify_admin_token(authorization)
    from app.api.fpt_shop import sync_fpt_shop, SyncRequest
    from datetime import date
    import logging
    logger = logging.getLogger("app.api.admin")
    logger.info("[ADMIN_DIAGNOSTIC] === BẮT ĐẦU CHẠY THỬ ĐỒNG BỘ FPT SHOP TỪ TRANG ADMIN ===")
    
    today = date.today()
    start_date = today.replace(day=1)
    req = SyncRequest(start_date=start_date, end_date=today)
    
    try:
        res = sync_fpt_shop(req, db)
        if res.success:
            logger.info(f"[ADMIN_DIAGNOSTIC] Đồng bộ FPT Shop THÀNH CÔNG! Đã tải {res.total_rows} dòng, {res.new_records} lỗi mới.")
        else:
            logger.error(f"[ADMIN_DIAGNOSTIC] Đồng bộ FPT Shop THẤT BẠI: {res.error_message}")
        return {
            "success": res.success,
            "data": res.model_dump(),
            "message": "Đồng bộ FPT Shop thành công!" if res.success else f"Thất bại: {res.error_message}"
        }
    except Exception as e:
        logger.error(f"[ADMIN_DIAGNOSTIC] Ngoại lệ khi chạy thử đồng bộ FPT: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Lỗi ngoại lệ: {e}"
        }
