import uuid
import threading
import tempfile
import os
import re
import logging
import time
from datetime import datetime
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.config import get_config
from fastapi.responses import FileResponse
from typing import Dict, Any

from app.services import backend_check, check_cam_service
from app.services import gsheet_sync
from app import config as app_config
import concurrent.futures
from app.api.schemas.common import ApiResponse

from app.services import warehouse_sync
from app.services.logging_utils import get_logger, session_id_var, action_id_var, job_id_var
logger = get_logger(__name__)

router = APIRouter(prefix="/api/camera", tags=["camera"])

JOB_STORE: Dict[str, Dict[str, Any]] = {}

@router.get("/warehouse/status", response_model=ApiResponse)
async def get_warehouse_status():
    status_data = warehouse_sync.get_warehouse_status()
    if status_data.get("status") == "ready":
        df = warehouse_sync.get_warehouse_df()
        if not df.empty:
            lc_count = len(check_cam_service.filter_shops(df, {"vaccine": False, "lc": True}))
            vx_count = len(check_cam_service.filter_shops(df, {"vaccine": True, "lc": False}))
            status_data["counts_by_mode"] = {
                "cam_lc": lc_count,
                "dvr_lc": lc_count,
                "cam_vx": vx_count,
                "dvr_vx": vx_count
            }
    return ApiResponse(success=True, status="ok", data=status_data)

def get_region_map_safe():
    try:
        return gsheet_sync.get_region_map()
    except Exception as e:
        logging.error(f"Error fetching region map: {e}")
        return {}

def do_sync_internal_dfs(dfs: dict) -> tuple[bool, list[dict], str]:
    df_out = dfs.get("df_out", pd.DataFrame())
    df_ticket = dfs.get("df_ticket", pd.DataFrame())
    df_online = dfs.get("df_online", pd.DataFrame())
    df_playback = dfs.get("df_playback", pd.DataFrame())
    df_ftel = dfs.get("df_ftel", pd.DataFrame())
    df_hdd = dfs.get("df_hdd", pd.DataFrame())
    
    has_data = (isinstance(df_out, pd.DataFrame) and not df_out.empty) or                (isinstance(df_ticket, pd.DataFrame) and not df_ticket.empty)
    if not has_data:
        return False, [], "Không có dữ liệu để đồng bộ"
        
    results = []
    try:
        if isinstance(df_ticket, pd.DataFrame) and not df_ticket.empty:
            df_errors = df_ticket[df_ticket['Danh sách Cam lỗi'].astype(str) != "DVR"].copy()
            cols_to_drop = ['Cam đã online', 'Cam cũ vẫn lỗi']
            df_errors = df_errors.drop(columns=[c for c in cols_to_drop if c in df_errors.columns])
            ok1, msg1 = gsheet_sync.sync_data(df_errors)
        else:
            ok1, msg1 = True, "Không có lỗi offline (bỏ qua)"
    except Exception as e:
        ok1, msg1 = False, f"Lỗi xử lý df_errors: {str(e)}"
    results.append({"type": "offline", "success": ok1, "message": msg1})
    
    try:
        ok2, msg2 = gsheet_sync.sync_back_online(df_online)
    except Exception as e:
        ok2, msg2 = False, f"Lỗi sync_back_online: {str(e)}"
    results.append({"type": "online", "success": ok2, "message": msg2})
    
    try:
        ok3, msg3 = gsheet_sync.sync_playback_errors(df_playback)
    except Exception as e:
        ok3, msg3 = False, f"Lỗi sync_playback_errors: {str(e)}"
    results.append({"type": "playback", "success": ok3, "message": msg3})
    
    try:
        ok4, msg4 = gsheet_sync.sync_dvr_errors(df_ftel)
    except Exception as e:
        ok4, msg4 = False, f"Lỗi sync_dvr_errors: {str(e)}"
    results.append({"type": "dvr", "success": ok4, "message": msg4})
    
    try:
        ok5, msg5 = gsheet_sync.sync_hdd_errors(df_hdd)
    except Exception as e:
        ok5, msg5 = False, f"Lỗi sync_hdd_errors: {str(e)}"
    results.append({"type": "hdd", "success": ok5, "message": msg5})
    
    success_count = sum(1 for r in results if r["success"])
    if success_count < 5:
        failed_msgs = [f"{r['type']}: {r['message']}" for r in results if not r["success"]]
        return False, results, " | ".join(failed_msgs)
    return True, results, "Đồng bộ thành công 5 sheets"

def check_camera_task(job_id: str, file_path: str, filter_options: dict, session_id: str = None, action_id: str = None, periodic: bool = None, interval_minutes: int = None):
    if session_id: session_id_var.set(session_id)
    if action_id: action_id_var.set(action_id)
    job_id_var.set(job_id)
    logger.info(f'Job {job_id} started', extra={'event': 'JOB_STARTED', 'metadata': {'mode': 'camera'}})
    JOB_STORE[job_id]["status"] = "running"
    JOB_STORE[job_id]["cycle"] = 0
    try:
        module_name = "CAM-VX" if filter_options.get("vaccine") else "CAM-LC"
        backend_check.signal_start(job_id)
        
        # 1. READ FILE
        try:
            if file_path == "AUTO_SYNC":
                df_in = warehouse_sync.get_warehouse_df()
            else:
                df_in = check_cam_service.read_input_file(file_path)
        except Exception as e:
            logger.error(f"Job {job_id} failed", exc_info=True, extra={"event": "JOB_FAILED"})
            JOB_STORE[job_id]["status"] = "failed"
            JOB_STORE[job_id]["error"] = f"Lỗi đọc file: {e}"
            return

        # 2. FILTER LOGIC
        if len(df_in.columns) < 3:
            logger.error(f"Job {job_id} failed", exc_info=True, extra={"event": "JOB_FAILED"})
            JOB_STORE[job_id]["status"] = "failed"
            JOB_STORE[job_id]["error"] = "Lỗi: File không đủ cột chuẩn (A, B, C...)"
            return

        df_process = check_cam_service.filter_shops(df_in, filter_options)
        
        if df_process.empty:
            logger.info(f"[{module_name}][JOB_COMPLETED] 0/0", extra={"event": "JOB_COMPLETED"})
            JOB_STORE[job_id]["status"] = "completed"
            JOB_STORE[job_id]["results"] = []
            return

        total_shops = len(df_process)
        JOB_STORE[job_id]["total"] = total_shops
        region_map = get_region_map_safe()

        # 3. IDENTIFY COLUMNS
        col_map = check_cam_service.detect_columns(df_process)
        if not col_map.get("ip"):
            logger.error(f"Job {job_id} failed", exc_info=True, extra={"event": "JOB_FAILED"})
            JOB_STORE[job_id]["status"] = "failed"
            JOB_STORE[job_id]["error"] = "Không tìm thấy cột IP!"
            return

        # 4. PERIODIC CONFIGURATION
        cfg = app_config.get_config()
        cc_cfg = cfg.get("check_cam", {})
        is_periodic = periodic if periodic is not None else cc_cfg.get("periodic_enabled", False)
        interval_mins = interval_minutes if interval_minutes is not None else cc_cfg.get("periodic_interval_minutes", 15)
        recovery_sheet = cc_cfg.get("recovery_sheet_name", "Cam chập chờn")
        
        cycle = 0
        prev_camera_status = {}
        total_recovered_count = 0
        
        while not backend_check.is_stopped(job_id):
            cycle += 1
            JOB_STORE[job_id]["cycle"] = cycle
            JOB_STORE[job_id]["cycle_status"] = "scanning"
            JOB_STORE[job_id]["progress"] = 0
            JOB_STORE[job_id]["total"] = total_shops
            
            # Fresh known errors
            known_errors = {}
            known_tickets = {}
            try:
                cfg_loop = app_config.get_config()
                url_sheet = cfg_loop.get("check_cam", {}).get(
                    "known_errors_csv_url",
                    "https://docs.google.com/spreadsheets/d/1hK2NYEjELl-8qapOQ72nS3E2iKrOAz9BwsLACZDcEaQ/export?format=csv&gid=0",
                )
                known_errors, known_tickets = check_cam_service.load_known_errors_and_tickets_from_csv(url_sheet)
            except Exception:
                pass
                
            old_err_count = sum(len(v) if isinstance(v, list) else 0 for v in known_errors.values())
            JOB_STORE[job_id]["metrics"] = {
                "total_old_errors": old_err_count,
                "new_errors": 0,
                "resolved": 0,
                "scanned": 0,
                "recovered_count": total_recovered_count
            }
            
            completed = 0
            results = []
            cycle_start_time = time.time()
            
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=backend_check.MAX_WORKERS)
            try:
                def _wrap_process(r, cm, idx):
                    backend_check.set_current_job_id(job_id)
                    shop_code = str(r[cm["code"]]).strip() if cm.get("code") else "Unknown"
                    ip = str(r[cm["ip"]]).strip() if cm.get("ip") else "Unknown"
                    logger.info(f"[{module_name}][C{cycle}][{idx+1:03d}/{total_shops}] Shop {shop_code} | IP={ip}", extra={"event": "SHOP_START", "metadata": {"shop": shop_code, "ip": ip, "index": idx+1, "total": total_shops, "cycle": cycle}})
                    t0 = time.time()
                    try:
                        res = backend_check.process_single_ip(r, cm)
                        return res, t0, shop_code, idx, ip
                    except Exception as e:
                        logger.error(f"[{module_name}][C{cycle}][{idx+1:03d}/{total_shops}] Shop {shop_code} | ERROR={type(e).__name__}", extra={"event": "SHOP_ERROR"})
                        return [], t0, shop_code, idx, ip

                futures = {executor.submit(_wrap_process, row, col_map, i): i for i, row in df_process.reset_index(drop=True).iterrows()}
                
                for f in concurrent.futures.as_completed(futures):
                    if backend_check.is_stopped(job_id):
                        break
                    completed += 1
                    JOB_STORE[job_id]["progress"] = completed
                    if completed % 10 == 0 or completed == total_shops:
                        logger.info(f"[{module_name}][C{cycle}][JOB_PROGRESS] {completed}/{total_shops} | {completed*100/total_shops:.2f}%", extra={"event": "JOB_PROGRESS", "metadata": {"processed": completed, "total": total_shops, "cycle": cycle}})
                    
                    try:
                        res_list, t0, shop_code, shop_idx, ip = f.result()
                        dur = int((time.time() - t0) * 1000)
                        status_str = "ONLINE" if (res_list and all(x.get('TrangThai') == 'Online' for x in res_list)) else ("OFFLINE/ERROR" if res_list else "OFFLINE")
                        logger.info(f"[{module_name}][C{cycle}][{shop_idx+1:03d}/{total_shops}] Shop {shop_code} | {status_str} | {dur}ms", extra={"event": "SHOP_RESULT", "metadata": {"shop": shop_code, "status": status_str, "duration_ms": dur, "cycle": cycle}})
                        
                        if res_list:
                            for item in res_list:
                                if item['TrangThai'] != 'Online':
                                    shop_c = str(item['MaShop']).strip()
                                    detail = str(item['ChiTiet'])
                                    cam_code = None
                                    if "Đầu ghi" in detail:
                                        m = re.search(r'(?:Camera\s+|CH)(\d+)', detail, re.IGNORECASE)
                                        if m:
                                            num = int(m.group(1))
                                            cam_code = f"CH{num:02d}"
                                    
                                    if cam_code and isinstance(known_errors, dict) and shop_c in known_errors:
                                        target_shop = known_errors.get(shop_c)
                                        if isinstance(target_shop, list) and cam_code in target_shop:
                                            item['TrangThai'] = f"Lỗi cũ ({item['TrangThai']})"
                                        else:
                                            item['TrangThai'] = f"LỖI MỚI ({item['TrangThai']})"
                                    elif item['TrangThai'] != 'Online':
                                        if known_errors: 
                                            item['TrangThai'] = f"LỖI MỚI ({item['TrangThai']})"

                                if "LỖI MỚI" in str(item.get('TrangThai', '')):
                                    JOB_STORE[job_id]["metrics"]["new_errors"] += 1
                                if "Online" in str(item.get('TrangThai', '')):
                                    s_code = str(item.get('MaShop', '')).strip()
                                    cam_detail = str(item.get('ChiTiet', ''))
                                    if s_code in known_errors and cam_detail in known_errors.get(s_code, []):
                                        JOB_STORE[job_id]["metrics"]["resolved"] += 1

                            results.extend(res_list)
                            JOB_STORE[job_id]["metrics"]["scanned"] = len(results)
                            JOB_STORE[job_id]["results"] = results
                    except Exception:
                        pass
            finally:
                executor.shutdown(wait=False)
                
            if backend_check.is_stopped(job_id):
                break
                
            # Intermittent / Recovery detection
            current_cycle_status = {}
            cycle_recovered = []
            
            for item in results:
                s_c = str(item.get('MaShop', '')).strip()
                cam_det = str(item.get('ChiTiet', '')).strip()
                tt = str(item.get('TrangThai', '')).strip()
                k = (s_c, cam_det)
                current_cycle_status[k] = tt
                
                if cycle > 1:
                    prev_tt = prev_camera_status.get(k, '')
                    is_now_online = "Online" in tt
                    was_offline = prev_tt and ("Online" not in prev_tt)
                    if is_now_online and was_offline:
                        cycle_recovered.append({
                            "Mã shop": s_c,
                            "Tên shop": str(item.get('TenShop', '')),
                            "Vùng": region_map.get(s_c, ''),
                            "Camera": cam_det,
                            "Chu kỳ": f"Chu kỳ #{cycle}",
                            "Thời gian": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
                            "Trạng thái": f"Offline chu kỳ #{cycle-1} -> Online chu kỳ #{cycle}"
                        })

            prev_camera_status = current_cycle_status
            
            if cycle_recovered:
                total_recovered_count += len(cycle_recovered)
                try:
                    ok_sync, msg_sync = gsheet_sync.sync_intermittent_cam(cycle_recovered, sheet_name=recovery_sheet)
                    logger.info(f"[{module_name}][SYNC_INTERMITTENT] Cycle #{cycle}: {msg_sync}")
                except Exception as ex_s:
                    logger.error(f"[{module_name}][SYNC_INTERMITTENT_ERR] {ex_s}")

            # SPLIT & METRICS
            results_dict_dfs = check_cam_service.generate_ticket_dataframe(
                results,
                region_file=region_map,
                create_data_list=[],
                known_errors=known_errors,
                known_tickets=known_tickets
            )
            
            new_err_count = sum(1 for r in results if "LỖI MỚI" in str(r.get('TrangThai', '')) or "Lá»–I Má»šI" in str(r.get('TrangThai', '')))
            resolved_count = 0
            online_count = 0
            offline_count = 0
            for r in results:
                tt = str(r.get('TrangThai', ''))
                if "Online" in tt:
                    online_count += 1
                    s_code = str(r.get('MaShop', '')).strip()
                    cam_detail = str(r.get('ChiTiet', ''))
                    if s_code in known_errors and cam_detail in known_errors.get(s_code, []):
                        resolved_count += 1
                elif "Analog" not in tt and "Dòng khác" not in tt:
                    offline_count += 1
                    
            dur = time.time() - cycle_start_time
            mins = int(dur // 60)
            secs = int(dur % 60)
            dur_str = f"{mins:02d}m{secs:02d}s"
            
            JOB_STORE[job_id]["metrics"] = {
                "total_old_errors": old_err_count,
                "new_errors": new_err_count,
                "resolved": resolved_count,
                "scanned": len(results),
                "online": online_count,
                "offline": offline_count,
                "recovered_count": total_recovered_count,
                "duration": dur
            }
            
            def df_to_dict(df):
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return df.fillna("").to_dict("records")
                return []
                
            JOB_STORE[job_id]["results_dict"] = {
                "total": df_to_dict(results_dict_dfs.get("df_out")),
                "playback": df_to_dict(results_dict_dfs.get("df_playback")),
                "ftel": df_to_dict(results_dict_dfs.get("df_ftel")),
                "hdd": df_to_dict(results_dict_dfs.get("df_hdd")),
            }
            JOB_STORE[job_id]["_internal_dfs"] = results_dict_dfs
            JOB_STORE[job_id]["results"] = results
            
            # Auto-sync to Google Sheets after each scan/cycle
            auto_sync_enabled = cc_cfg.get("periodic_auto_sync", True)
            if auto_sync_enabled:
                try:
                    logger.info(f"[{module_name}][C{cycle}] Đang tự động đồng bộ kết quả chu kỳ #{cycle} lên Google Sheets...", extra={"event": "AUTO_SYNC_START", "metadata": {"cycle": cycle}})
                    ok_all, sync_res, sync_msg = do_sync_internal_dfs(results_dict_dfs)
                    JOB_STORE[job_id]["last_sync_time"] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                    JOB_STORE[job_id]["last_sync_status"] = "success" if ok_all else "partial_error"
                    JOB_STORE[job_id]["last_sync_message"] = sync_msg
                    logger.info(f"[{module_name}][C{cycle}] Tự động đồng bộ chu kỳ #{cycle} hoàn tất: {sync_msg}", extra={"event": "AUTO_SYNC_DONE", "metadata": {"cycle": cycle, "success": ok_all, "message": sync_msg}})
                except Exception as ex_sync_all:
                    logger.error(f"[{module_name}][C{cycle}] Lỗi tự động đồng bộ: {ex_sync_all}")
                    JOB_STORE[job_id]["last_sync_status"] = "error"
                    JOB_STORE[job_id]["last_sync_message"] = str(ex_sync_all)

            summary = f"[{module_name}][CYCLE_{cycle}_DONE] {completed}/{total_shops} | DURATION={dur_str} | RECOVERED={total_recovered_count}"
            logger.info(summary, extra={"event": "CYCLE_COMPLETED", "metadata": JOB_STORE[job_id]["metrics"]})
            
            if not is_periodic:
                break
                
            # Periodic countdown
            wait_seconds = max(10, interval_mins * 60)
            JOB_STORE[job_id]["cycle_status"] = "waiting"
            JOB_STORE[job_id]["wait_total_seconds"] = wait_seconds
            JOB_STORE[job_id]["skip_wait"] = False
            
            for sec_left in range(wait_seconds, 0, -1):
                if backend_check.is_stopped(job_id) or JOB_STORE[job_id].get("skip_wait", False):
                    break
                JOB_STORE[job_id]["next_cycle_seconds"] = sec_left
                time.sleep(1)
            JOB_STORE[job_id]["skip_wait"] = False

        if backend_check.is_stopped(job_id):
            JOB_STORE[job_id]["status"] = "cancelled"
            logger.info(f"[{module_name}][JOB_STOPPED] Cycle #{cycle}", extra={"event": "JOB_STOPPED"})
        else:
            JOB_STORE[job_id]["status"] = "completed"
            logger.info(f"[{module_name}][JOB_COMPLETED] Finished {cycle} cycles", extra={"event": "JOB_COMPLETED"})
            
    except Exception as e:
        logger.error(f"Job {job_id} failed", exc_info=True, extra={"event": "JOB_FAILED"})
        JOB_STORE[job_id]["status"] = "failed"
        JOB_STORE[job_id]["error"] = str(e)
    finally:
        backend_check.clear_stop(job_id)
        try: os.remove(file_path)
        except: pass

def monitor_camera_task(job_id: str, file_path: str, filter_options: dict, session_id: str = None, action_id: str = None):
    if session_id: session_id_var.set(session_id)
    if action_id: action_id_var.set(action_id)
    job_id_var.set(job_id)
    logger.info(f'Job {job_id} started', extra={'event': 'JOB_STARTED', 'metadata': {'mode': 'monitor'}})
    JOB_STORE[job_id]["status"] = "running"
    JOB_STORE[job_id]["cycle"] = 0
    try:
        module_name = "CAM-NO-DATA"
        backend_check.signal_start(job_id)
        try:
            if file_path == "AUTO_SYNC":
                df_in = warehouse_sync.get_warehouse_df()
            else:
                df_in = check_cam_service.read_input_file(file_path)
        except Exception as e:
            logger.error(f"Job {job_id} failed", exc_info=True, extra={"event": "JOB_FAILED"})
            JOB_STORE[job_id]["status"] = "failed"
            JOB_STORE[job_id]["error"] = f"Lỗi đọc file: {e}"
            return

        if len(df_in.columns) < 3:
            logger.error(f"Job {job_id} failed", exc_info=True, extra={"event": "JOB_FAILED"})
            JOB_STORE[job_id]["status"] = "failed"
            JOB_STORE[job_id]["error"] = "Lỗi: File không đủ cột chuẩn (A, B, C...)"
            return

        df_process = check_cam_service.filter_shops(df_in, filter_options)
        if df_process.empty:
            logger.info(f"Job {job_id} completed", extra={"event": "JOB_COMPLETED", "metadata": JOB_STORE[job_id].get("metrics", {})})
            JOB_STORE[job_id]["status"] = "completed"
            JOB_STORE[job_id]["results"] = []
            return

        JOB_STORE[job_id]["total"] = len(df_process)
        col_map = check_cam_service.detect_columns(df_process)
        if not col_map.get("ip"):
            logger.error(f"Job {job_id} failed", exc_info=True, extra={"event": "JOB_FAILED"})
            JOB_STORE[job_id]["status"] = "failed"
            JOB_STORE[job_id]["error"] = "Không tìm thấy cột IP!"
            return

        loop_count = 0
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=backend_check.MAX_WORKERS)
        try:
            while not backend_check.is_stopped(job_id):
                loop_count += 1
                JOB_STORE[job_id]["cycle"] = loop_count
                start_time = time.time()
                
                def _wrap_dvr(r, cm):
                    backend_check.set_current_job_id(job_id)
                    return backend_check.check_dvr_status(r, cm)
                futures = {pool.submit(_wrap_dvr, row, col_map): i for i, row in df_process.iterrows()}
                completed = 0
                
                status_dict = JOB_STORE[job_id].get("results_dict", {})
                history_list = JOB_STORE[job_id].get("history", [])
                
                for f in concurrent.futures.as_completed(futures):
                    if backend_check.is_stopped(job_id): break
                    completed += 1
                    JOB_STORE[job_id]["progress"] = completed
                    if completed % 100 == 0 or completed == len(df_process):
                        logger.info(f"Progress {completed}/{len(df_process)}", extra={"event": "JOB_PROGRESS", "metadata": {"processed": completed, "total": len(df_process)}})
                    try:
                        res = f.result()
                        if res and "Mã shop" in res and "IP" in res:
                            key = f"{res['Mã shop']}_{res['IP']}"
                            old_res = status_dict.get(key)
                            
                            if not old_res or old_res.get("Kết quả") != res.get("Kết quả"):
                                history_list.append(res)
                                
                            status_dict[key] = res
                    except: pass
                
                JOB_STORE[job_id]["results_dict"] = status_dict
                JOB_STORE[job_id]["history"] = history_list
                JOB_STORE[job_id]["results"] = list(status_dict.values())
                
                if backend_check.is_stopped(job_id): break
                
                elapsed = time.time() - start_time
                wait_time = backend_check.MIN_CYCLE_TIME - elapsed
                if wait_time > 0:
                    for _ in range(int(wait_time)):
                        if backend_check.is_stopped(job_id): break
                        time.sleep(1)
        finally:
            pool.shutdown(wait=False)
            
        if backend_check.is_stopped(job_id):
            
            metrics = JOB_STORE[job_id].get("metrics", {})
            dur = metrics.get("duration", 0)
            mins = int(dur // 60)
            secs = int(dur % 60)
            dur_str = f"{mins:02d}m{secs:02d}s"
            
            summary = f"[{module_name}][JOB_STOPPED] {completed}/{total_shops} | DURATION={dur_str}"
            logger.info(summary, extra={"event": "JOB_STOPPED", "metadata": metrics})

            JOB_STORE[job_id]["status"] = "cancelled"
        else:
            logger.info(f"Job {job_id} completed", extra={"event": "JOB_COMPLETED"})
            JOB_STORE[job_id]["status"] = "completed"
    except Exception as e:
        logger.error(f"Job {job_id} failed", exc_info=True, extra={"event": "JOB_FAILED"})
        JOB_STORE[job_id]["status"] = "failed"
        JOB_STORE[job_id]["error"] = str(e)
    finally:
        backend_check.clear_stop(job_id)
        try: os.remove(file_path)
        except: pass


@router.post("/jobs", response_model=ApiResponse)
async def create_camera_job(
    file: Optional[UploadFile] = File(None),
    vaccine: bool = Form(False),
    lc: bool = Form(False),
    mode: str = Form("camera"),
    periodic: Optional[bool] = Form(None),
    interval_minutes: Optional[int] = Form(None)
):
    job_id = str(uuid.uuid4())
    
    if file:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".csv" if file.filename.endswith(".csv") else ".xlsx")
        os.close(tmp_fd)
        with open(tmp_path, "wb") as buffer:
            buffer.write(await file.read())
    else:
        status_data = warehouse_sync.get_warehouse_status()
        if status_data["status"] == "ready":
            tmp_path = "AUTO_SYNC"
        else:
            config = get_config()
            tmp_path = config.get("paths", {}).get("warehouse_file", "")
            if not tmp_path or not os.path.exists(tmp_path):
                raise HTTPException(status_code=400, detail="Vui lòng tải lên file hoặc đợi tự động tải Warehouse.")
        
    filter_options = {"vaccine": vaccine, "lc": lc}
    
    JOB_STORE[job_id] = {
        "status": "queued",
        "progress": 0,
        "total": 0,
        "results": [],
        "error": None,
        "mode": mode,
        "metrics": {},
        "results_dict": {},
        "cycle": 0
    }
    
    target = monitor_camera_task if mode == "monitor" else check_camera_task
    session_id = session_id_var.get()
    action_id = action_id_var.get()
    logger.info(f'Job {job_id} created', extra={'event': 'JOB_CREATED', 'metadata': {'mode': mode}})
    if mode == "monitor":
        t = threading.Thread(target=monitor_camera_task, args=(job_id, tmp_path, filter_options, session_id, action_id))
    else:
        t = threading.Thread(target=check_camera_task, args=(job_id, tmp_path, filter_options, session_id, action_id, periodic, interval_minutes))
    t.start()
    
    return ApiResponse(success=True, status="ok", data={"job_id": job_id})

@router.get("/jobs/{job_id}", response_model=ApiResponse)
async def get_camera_job(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
        
    data = JOB_STORE[job_id].copy()
    
    # [API_RESPONSE] trace
    try:
        from loguru import logger
        import logging
        log = logger if 'logger' in globals() else logging.getLogger("api")
        if data.get("status") in ["completed", "failed"]:
            for r in data.get("results", []):
                if str(r.get("MaShop")) == "80953" and str(r.get("ChiTiet")) == "CH07":
                    log.info("[API_RESPONSE]\njob_id=%s\nshop=80953\nchannel=CH07\nonline_date=%s", 
                             job_id, r.get("LastRecordTime"))
    except Exception as e:
        pass
        
    if "_internal_dfs" in data:
        del data["_internal_dfs"]
    return ApiResponse(success=True, status="ok", data=data)

@router.post("/jobs/{job_id}/skip-wait", response_model=ApiResponse)
async def skip_camera_job_wait(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
    JOB_STORE[job_id]["skip_wait"] = True
    JOB_STORE[job_id]["next_cycle_seconds"] = 0
    return ApiResponse(success=True, status="ok", message="Bỏ qua chờ, bắt đầu chu kỳ kế tiếp")

@router.post("/jobs/{job_id}/cancel", response_model=ApiResponse)
async def cancel_camera_job(job_id: str):
    if job_id in JOB_STORE and JOB_STORE[job_id]["status"] in ["queued", "running"]:
        backend_check.signal_stop(job_id)
    return ApiResponse(success=True, status="ok", message="Cancel signal sent")

@router.post("/jobs/{job_id}/export")
async def export_camera_job(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = JOB_STORE[job_id]
    if job["mode"] == "monitor":
        df = pd.DataFrame(job["results"])
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(tmp_fd)
        df.to_excel(tmp_path, index=False)
        return FileResponse(tmp_path, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename="monitor_export.xlsx")
        
    dfs = job.get("_internal_dfs", {})
    df_out = dfs.get("df_out", pd.DataFrame())
    
    if df_out.empty:
        raise HTTPException(status_code=400, detail="No data to export")
        
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(tmp_fd)
    
    try:
        check_cam_service.generate_camera_export_excel(dfs, tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
            
    return FileResponse(tmp_path, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename="check_camera_export.xlsx")

@router.post("/jobs/{job_id}/sync", response_model=ApiResponse)
def sync_camera_job(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = JOB_STORE[job_id]
    if job["mode"] == "monitor":
        return ApiResponse(success=False, status="error", message="Cannot sync monitor jobs")
        
    dfs = job.get("_internal_dfs", {})
    ok, results, msg = do_sync_internal_dfs(dfs)
    if not ok:
        return ApiResponse(success=False, status="error", message=msg, data=results)
    return ApiResponse(success=True, status="ok", message=msg, data=results)
