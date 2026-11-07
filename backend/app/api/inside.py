from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import json
import logging
from app.core.config import BROWSER_DATA_DIR
from app.services.fpt_shop.browser_session import FPTBrowserSession
from app.services.long_chau.login.browser_session import LongChauBrowserSession
from app.services.vaccine.login.browser_session import VaccineBrowserSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inside", tags=["Inside Account"])

INSIDE_CREDS_FILE = os.path.join(BROWSER_DATA_DIR, "inside_credentials.json")

class InsideCredsRequest(BaseModel):
    username: str
    password: Optional[str] = ""

class InsideCredsResponse(BaseModel):
    success: bool
    username: str = ""
    password: str = ""
    has_password: bool = False

@router.get("/creds", response_model=InsideCredsResponse)
def get_inside_creds():
    username = ""
    password = ""
    
    # 1. Try reading inside_credentials.json
    if os.path.exists(INSIDE_CREDS_FILE):
        try:
            with open(INSIDE_CREDS_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                username = d.get("username", "")
                password = d.get("password", "")
        except Exception as e:
            logger.warning(f"Could not read inside_credentials.json: {e}")
            
    # 2. Fallback to existing profile creds if not found
    if not username:
        for f_name in ["fpt-sso-profile_creds.json", "fpt-shop-profile_creds.json", "vaccine-profile_creds.json"]:
            p = os.path.join(BROWSER_DATA_DIR, f_name)
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        d = json.load(f)
                        if d.get("username"):
                            username = d.get("username", "")
                            password = d.get("password", "")
                            break
                except Exception:
                    pass

    return InsideCredsResponse(
        success=True,
        username=username,
        password=password,
        has_password=bool(password)
    )

@router.post("/creds")
def save_inside_creds(req: InsideCredsRequest):
    username = (req.username or "").strip()
    password = req.password or ""
    
    if not username:
        raise HTTPException(status_code=400, detail="Vui lòng nhập tên tài khoản Inside.")
        
    creds_data = {"username": username, "password": password, "otp": ""}
    
    # 1. Save to inside_credentials.json
    try:
        os.makedirs(BROWSER_DATA_DIR, exist_ok=True)
        with open(INSIDE_CREDS_FILE, "w", encoding="utf-8") as f:
            json.dump(creds_data, f, indent=2)
        logger.info(f"Saved inside_credentials.json for user {username}")
    except Exception as e:
        logger.error(f"Error saving inside_credentials.json: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu tài khoản Inside: {e}")

    # 2. Sync to all 3 chain profiles so they can auto-login
    for f_name in ["fpt-shop-profile_creds.json", "fpt-sso-profile_creds.json", "vaccine-profile_creds.json"]:
        try:
            p = os.path.join(BROWSER_DATA_DIR, f_name)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(creds_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not sync creds to {f_name}: {e}")

    # 3. Update in-memory session objects
    try:
        FPTBrowserSession.get_instance().temp_creds = creds_data
    except Exception:
        pass
    try:
        LongChauBrowserSession.get_instance().temp_creds = creds_data
    except Exception:
        pass
    try:
        VaccineBrowserSession.get_instance().temp_creds = creds_data
    except Exception:
        pass

    return {
        "success": True,
        "message": "Đã lưu tài khoản Inside vĩnh viễn trên máy chủ.",
        "username": username
    }
