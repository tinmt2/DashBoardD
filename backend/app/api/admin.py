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

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "admin_config.json")
START_TIME = time.time()

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _get_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Default config
    default_cfg = {
        "admin_username": "admin",
        "admin_password_hash": _hash_pw("admin@123"),
        "active_tokens": []
    }
    _save_config(default_cfg)
    return default_cfg

def _save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

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
    if not authorization:
        raise HTTPException(status_code=401, detail="Chưa có token xác thực!")
    token = authorization.replace("Bearer ", "").strip()
    cfg = _get_config()
    valid_tokens = [t["token"] for t in cfg.get("active_tokens", [])]
    if token not in valid_tokens:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập Admin đã hết hạn!")
    return {"valid": True, "username": cfg.get("admin_username", "admin")}

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Yêu cầu quyền Admin!")
    token = authorization.replace("Bearer ", "").strip()
    cfg = _get_config()
    valid_tokens = [t["token"] for t in cfg.get("active_tokens", [])]
    if token not in valid_tokens:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ!")
    
    if _hash_pw(req.old_password) != cfg.get("admin_password_hash"):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng!")
    
    if len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 4 ký tự!")
        
    cfg["admin_password_hash"] = _hash_pw(req.new_password)
    _save_config(cfg)
    return {"success": True, "message": "Đổi mật khẩu Admin thành công!"}

@router.get("/overview")
def admin_overview(db: Session = Depends(get_db)):
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
            recent_notifs.append({
                "id": n.id,
                "chain": n.chain,
                "title": n.title,
                "message": n.message,
                "status": n.status,
                "created_at": n.created_at.isoformat() if n.created_at else None
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
