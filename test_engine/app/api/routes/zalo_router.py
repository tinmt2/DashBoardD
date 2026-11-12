import asyncio




import logging




from typing import Dict, Any, Optional




from fastapi import APIRouter, BackgroundTasks, HTTPException




from pydantic import BaseModel









from app.api.schemas.common import ApiResponse




from app.services.zalo_monitor_service import zalo_monitor_service




from app.services.zalo_web_adapter import zalo_web_adapter




from app.config import get_config, save_config, reload_config









logger = logging.getLogger(__name__)









router = APIRouter(prefix="/api/zalo", tags=["zalo-monitor"])









class StartMonitoringRequest(BaseModel):




    group_name: str




    batch_interval_minutes: int = 10









class SetBatchIntervalRequest(BaseModel):
    batch_interval_minutes: int


class OpenBrowserRequest(BaseModel):




    headless: bool = False









class ClearDataRequest(BaseModel):




    clear_db: bool = True




    clear_sheet: bool = True









class UpdateApiKeyRequest(BaseModel):




    gemini_api_key: str









class UpdateFixedGroupRequest(BaseModel):




    group_name: str









class SelectGroupRequest(BaseModel):




    group_name: str









class ScanHistoryRequest(BaseModel):




    group_name: Optional[str] = None




    scroll_count: int = 5









@router.get("/status", response_model=ApiResponse)




async def get_status(include_messages: bool = True):




    """Lấy trạng thái tổng quan của Zalo Monitor (kết nối, thống kê, bảng log)."""




    try:




        data = zalo_monitor_service.get_full_state(include_messages=include_messages)




        cfg = get_config()




        data["fixed_group_name"] = cfg.get("zalo_monitor", {}).get("fixed_group_name", "")




        return ApiResponse(success=True, status="ok", data=data)




    except Exception as e:




        logger.error(f"Lỗi lấy trạng thái Zalo Monitor: {e}")




        return ApiResponse(success=False, status="error", message=str(e))









@router.post("/save-fixed-group", response_model=ApiResponse)




async def save_fixed_group(payload: UpdateFixedGroupRequest):




    """Lưu cố định 1 tên nhóm duy nhất vào config.json và khóa adapter vào nhóm này."""




    try:




        cfg = reload_config()




        group = payload.group_name.strip()




        cfg.setdefault("zalo_monitor", {})["fixed_group_name"] = group




        save_config(cfg)




        reload_config()




        zalo_web_adapter.active_group_name = group




        zalo_monitor_service.log_event(f"Đã cố định nhóm giám sát duy nhất: '{group}'")




        




        # Nếu trình duyệt đang mở và có group, chuyển thẳng vào nhóm




        if group and zalo_web_adapter.driver:




            await asyncio.to_thread(zalo_web_adapter.select_group, group)









        return ApiResponse(success=True, status="ok", message=f"Đã lưu nhóm cố định '{group}' thành công!")




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))

@router.post("/set-batch-interval", response_model=ApiResponse)
async def set_batch_interval(payload: SetBatchIntervalRequest):
    """Cập nhật chu kỳ đồng bộ Google Sheets (phút) và lưu bền vững vào config.json."""
    try:
        minutes = max(1, min(1440, payload.batch_interval_minutes))
        zalo_monitor_service.batch_interval_minutes = minutes
        
        cfg = reload_config()
        cfg.setdefault("zalo_monitor", {})["batch_interval_minutes"] = minutes
        save_config(cfg)
        reload_config()
        
        zalo_monitor_service.log_event(f"Đã cập nhật chu kỳ đồng bộ thành: {minutes} phút")
        return ApiResponse(success=True, status="ok", message=f"Đã cập nhật chu kỳ thành {minutes} phút.")
    except Exception as e:
        logger.error(f"Lỗi cập nhật chu kỳ: {e}")
        return ApiResponse(success=False, status="error", message=str(e))










@router.post("/select-group", response_model=ApiResponse)




async def select_group(payload: SelectGroupRequest):




    """Chuyển ngay lập tức đến nhóm chat trên Zalo Web."""




    try:




        group = payload.group_name.strip()




        if not group:




            return ApiResponse(success=False, status="error", message="Tên nhóm không được để trống")




        




        # Tự động mở trình duyệt nếu chưa mở




        if not zalo_web_adapter.driver:




            await asyncio.to_thread(zalo_web_adapter.open_browser, False)




            await asyncio.sleep(2)









        switched = await asyncio.to_thread(zalo_web_adapter.select_group, group)




        zalo_monitor_service.log_event(f"Yêu cầu chuyển sang nhóm: '{group}' ({'Thành công' if switched else 'Đang tìm kiếm'})")




        return ApiResponse(




            success=switched, 




            status="ok" if switched else "warning", 




            message=f"Đã chuyển sang nhóm '{group}' trên Zalo Web." if switched else f"Đang điều hướng đến nhóm '{group}'..."




        )




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))









@router.post("/auto-connect", response_model=ApiResponse)




async def auto_connect():




    """Tự động kiểm tra session Zalo và khởi động trình duyệt nếu đã có phiên đăng nhập."""




    try:




        if zalo_web_adapter.driver or getattr(zalo_web_adapter, "_is_opening", False):




            return ApiResponse(success=True, status="ok", message="Trình duyệt đã được kết nối sẵn.")









        if zalo_web_adapter.has_saved_session():




            logger.info("Phát hiện session Zalo profile đã lưu, tự động mở trình duyệt...")




            await asyncio.to_thread(zalo_web_adapter.open_browser, False)




            zalo_monitor_service.log_event("Tự động khôi phục phiên Zalo Web thành công (không cần đăng nhập lại).")




            




            # Nếu đã có fixed_group_name, tự động chọn nhóm đó luôn




            cfg = get_config()




            target_group = cfg.get("zalo_monitor", {}).get("fixed_group_name")




            if target_group:




                await asyncio.sleep(2)




                await asyncio.to_thread(zalo_web_adapter.select_group, target_group)









            return ApiResponse(success=True, status="ok", message="Tự động kết nối Zalo Web thành công.")




        else:




            return ApiResponse(success=False, status="no_session", message="Chưa tìm thấy session lưu trữ Zalo Web.")




    except Exception as e:




        logger.warning(f"Lỗi auto_connect Zalo: {e}")




        return ApiResponse(success=False, status="error", message=str(e))









@router.post("/open-browser", response_model=ApiResponse)
async def open_zalo_browser(payload: OpenBrowserRequest):
    """Mở trình duyệt chuyên dụng để người dùng đăng nhập Zalo Web."""
    try:
        result = await asyncio.to_thread(zalo_web_adapter.open_browser, headless=payload.headless)
        if isinstance(result, dict):
            success = result.get("success", True)
            message = result.get("message", "Trình duyệt đã được mở.")
            data = result
        else:
            success = bool(result)
            message = "Trình duyệt đã được mở. Vui lòng đăng nhập nếu chưa đăng nhập."
            data = {"success": success}

        zalo_monitor_service.log_event(message)
        return ApiResponse(success=success, status="ok" if success else "error", message=message, data=data)
    except Exception as e:
        return ApiResponse(success=False, status="error", message=f"Không thể mở trình duyệt: {str(e)}")









@router.post("/close-browser", response_model=ApiResponse)




async def close_zalo_browser():




    """Đóng trình duyệt Zalo Web."""




    try:




        await asyncio.to_thread(zalo_web_adapter.close_browser)




        zalo_monitor_service.stop_monitoring()




        return ApiResponse(success=True, status="ok", message="Đã đóng trình duyệt Zalo Web.")




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))









@router.get("/conversations", response_model=ApiResponse)




async def get_conversations():




    """Lấy danh sách các nhóm/cuộc trò chuyện đang mở trên Zalo Web."""




    try:




        conversations = await asyncio.to_thread(zalo_web_adapter.get_conversation_list)




        return ApiResponse(success=True, status="ok", data=conversations)




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))









@router.post("/start", response_model=ApiResponse)




async def start_monitoring(payload: StartMonitoringRequest):




    """Bắt đầu phiên giám sát tin nhắn mới."""




    try:




        if not zalo_web_adapter.driver:
            await asyncio.to_thread(zalo_web_adapter.open_browser, False)
        cfg = get_config()




        fixed_group = cfg.get("zalo_monitor", {}).get("fixed_group_name")




        target_group = fixed_group or payload.group_name









        zalo_monitor_service.start_monitoring(




            group_name=target_group,




            batch_interval_minutes=payload.batch_interval_minutes




        )




        return ApiResponse(success=True, status="ok", message=f"Đã bắt đầu giám sát duy nhất nhóm '{target_group}'.")




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))









@router.post("/stop", response_model=ApiResponse)




async def stop_monitoring():




    """Dừng phiên giám sát."""




    try:




        zalo_monitor_service.stop_monitoring()




        return ApiResponse(success=True, status="ok", message="Đã dừng giám sát.")




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))









@router.post("/scan-history", response_model=ApiResponse)




async def scan_history(payload: ScanHistoryRequest):




    """Đọc tin nhắn trong khoảng thời gian trước đó (cuộn ngược lịch sử chat)."""




    try:




        if not zalo_web_adapter.driver:
            await asyncio.to_thread(zalo_web_adapter.open_browser, False)
        cfg = get_config()




        target_group = payload.group_name or cfg.get("zalo_monitor", {}).get("fixed_group_name") or zalo_web_adapter.active_group_name




        if target_group:




            zalo_web_adapter.active_group_name = target_group




            await asyncio.to_thread(zalo_web_adapter.select_group, target_group)









        res = await zalo_monitor_service.scan_history_messages(scroll_count=payload.scroll_count)




        sync_res = res.get("sync_res", {})
        total_sheet = sync_res.get("total_on_sheet", 0) if isinstance(sync_res, dict) else 0
        return ApiResponse(
            success=True, 
            status="ok", 
            message=f"Đã quét xong {res['total_scanned']} tin và tự động đẩy lên Google Sheets thành công ({total_sheet} tin trên Sheet)."
        )




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))









@router.post("/sync-now", response_model=ApiResponse)




async def sync_now():




    """Đồng bộ thủ công ngay lập tức các tin nhắn sang Google Sheets (có đối soát)."""




    try:




        result = await zalo_monitor_service.sync_pending_to_gsheet(force_reconcile=True)




        if result.get("status") == "ok":




            added = result.get("synced_count", 0)




            total = result.get("total_on_sheet", 0)




            if added > 0:




                msg = f"Đã ghi thêm {added} tin nhắn mới vào Google Sheets. Tổng số trên Sheet: {total}."




            else:




                msg = f"Toàn bộ tin nhắn ({total} tin) đã có sẵn đầy đủ trên Google Sheets."




            return ApiResponse(success=True, status="ok", message=msg, data=result)




        else:




            return ApiResponse(success=False, status="error", message=result.get("message", "Lỗi đồng bộ"))




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))









@router.post("/clear-data", response_model=ApiResponse)




async def clear_data(payload: ClearDataRequest):




    """Xóa sạch các bản ghi quét cũ để làm mới từ đầu."""




    try:




        res = await asyncio.to_thread(




            zalo_monitor_service.clear_history_data,




            clear_db=payload.clear_db,




            clear_sheet=payload.clear_sheet




        )




        return ApiResponse(success=True, status="ok", message=res["message"])




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))









@router.post("/config-key", response_model=ApiResponse)




async def update_gemini_key(payload: UpdateApiKeyRequest):




    """Lưu Gemini API Key vào config.json."""




    try:




        cfg = reload_config()




        cfg.setdefault("zalo_monitor", {})["gemini_api_key"] = payload.gemini_api_key.strip()




        save_config(cfg)




        reload_config()




        zalo_monitor_service.log_event("Đã cập nhật Gemini API Key.")




        return ApiResponse(success=True, status="ok", message="Đã lưu Gemini API Key thành công!")




    except Exception as e:




        return ApiResponse(success=False, status="error", message=str(e))
