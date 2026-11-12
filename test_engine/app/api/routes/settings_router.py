from fastapi import APIRouter
from typing import Dict, Any

from app.config import get_config, save_config, reload_config
from app.api.schemas.common import ApiResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("", response_model=ApiResponse)
async def get_settings():
    config = get_config()
    # Mask sensitive Google Sheet details (not editable anyway in UI)
    safe_config = config.copy()
    if "gsheet" in safe_config:
        safe_config["gsheet"] = {
            "configured": True,
            "spreadsheet_id": "********" if config["gsheet"].get("spreadsheet_id") else "",
            "target_gid": config["gsheet"].get("target_gid"),
            "cred_file": config["gsheet"].get("cred_file")
        }
    return ApiResponse(success=True, status="ok", data=safe_config)

@router.put("", response_model=ApiResponse)
async def update_settings(payload: Dict[str, Any]):
    current_config = reload_config()
    
    # We only allow updating paths.warehouse_file from the UI
    if "paths" in payload and "warehouse_file" in payload["paths"]:
        current_config.setdefault("paths", {})["warehouse_file"] = payload["paths"]["warehouse_file"]

    if "check_cam" in payload and isinstance(payload["check_cam"], dict):
        cc = current_config.setdefault("check_cam", {})
        if "periodic_enabled" in payload["check_cam"]:
            cc["periodic_enabled"] = bool(payload["check_cam"]["periodic_enabled"])
        if "periodic_interval_minutes" in payload["check_cam"]:
            try:
                cc["periodic_interval_minutes"] = max(1, int(payload["check_cam"]["periodic_interval_minutes"]))
            except (ValueError, TypeError):
                pass
        if "recovery_sheet_name" in payload["check_cam"]:
            sheet_name = str(payload["check_cam"]["recovery_sheet_name"]).strip()
            if sheet_name:
                cc["recovery_sheet_name"] = sheet_name
        if "periodic_auto_sync" in payload["check_cam"]:
            cc["periodic_auto_sync"] = bool(payload["check_cam"]["periodic_auto_sync"])
        
    try:
        save_config(current_config)
        reload_config()
        return ApiResponse(success=True, status="completed", message="Cập nhật cấu hình thành công!")
    except Exception as e:
        return ApiResponse(success=False, status="error", message=f"Lỗi lưu cấu hình: {e}")
