from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.services.scheduler.auto_sync_service import AutoSyncService

router = APIRouter()


class AutoSyncConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    interval_minutes: Optional[int] = Field(None, ge=5, le=1440)
    sync_chains: Optional[List[str]] = None
    date_range_days: Optional[int] = Field(None, ge=1, le=365)


@router.get("/config")
def get_auto_sync_config():
    """
    Get the current automated background synchronization configuration and status.
    """
    service = AutoSyncService.get_instance()
    return {
        "success": True,
        "data": service.get_status_info()
    }


@router.post("/config")
def update_auto_sync_config(payload: AutoSyncConfigUpdate):
    """
    Update auto-sync configuration (toggle active, change interval, chains, date range).
    """
    service = AutoSyncService.get_instance()
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated_info = service.update_config(update_data)
    return {
        "success": True,
        "message": "Cấu hình tự động đồng bộ đã được cập nhật thành công.",
        "data": updated_info
    }


@router.post("/run-now")
def trigger_auto_sync_now():
    """
    Manually trigger an immediate background synchronization across configured chains.
    """
    service = AutoSyncService.get_instance()
    result = service.trigger_run_now()
    if not result.get("success"):
        raise HTTPException(status_code=409, detail=result.get("message"))
    return result
