import uuid
import tempfile
import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any, Optional

from app.api.schemas.common import ApiResponse
from app.services.ticket_scanner import TicketScanner
from app.services.check_ticket_scanner import CheckTicketScanner

from app.services import gsheet_sync

def normalize_ticket_df(df: pd.DataFrame) -> pd.DataFrame:
    COL_VUNG = "Vùng"
    COL_TEN = "Tên shop"
    COL_MA = "Mã shop"
    COL_TICKET = "Ticket"

    vung_keys = ['vùng', 'region', 'khu vực', 'location', 'miền']
    ten_keys = ['tên shop', 'ten_shop', 'shop name', 'tên ch']
    ma_keys = ['mã shop', 'ma_shop', 'shop code', 'mã kho', 'mã ch']
    ticket_keys = ['ticket_id', 'ticket id', 'id', 'ticket']

    def find_col(possible_keys, existing_cols):
        for k in possible_keys:
            for c in existing_cols:
                if str(c).lower().strip() == k:
                    return c
        return None

    cols = list(df.columns)
    
    actual_vung = find_col(vung_keys, cols)
    if not actual_vung and len(cols) > 0:
        sample_vals = [str(x).strip().lower() for x in df[cols[0]].dropna().head(5)]
        if any(any(reg in v for reg in ['miền', 'hà nội', 'hồ chí minh', 'hcm']) for v in sample_vals):
            actual_vung = cols[0]
    actual_ten = find_col(ten_keys, cols)
    actual_ma = find_col(ma_keys, cols)
    actual_ticket = find_col(ticket_keys, cols)

    rename_map = {}
    if actual_vung: rename_map[actual_vung] = COL_VUNG
    if actual_ten: rename_map[actual_ten] = COL_TEN
    if actual_ma: rename_map[actual_ma] = COL_MA
    if actual_ticket: rename_map[actual_ticket] = COL_TICKET
    
    df = df.rename(columns=rename_map)

    current_cols = list(df.columns)
    front_cols = []
    
    for c in [COL_VUNG, COL_TEN, COL_MA, COL_TICKET]:
        if c in current_cols:
            front_cols.append(c)
        else:
            df[c] = ""
            front_cols.append(c)

    remaining_cols = [c for c in current_cols if c not in front_cols]
    final_cols = front_cols + remaining_cols
    return df[final_cols]

router = APIRouter(prefix="/api/ticket", tags=["ticket"])

# Global state to persist the Selenium Driver across jobs (matches PyQt5 TicketWidget behavior)
# This keeps the Azure AD session alive.
GLOBAL_TICKET_DRIVER = None

JOB_STORE: Dict[str, Dict[str, Any]] = {}
TICKET_CACHE: Dict[str, Any] = {}

@router.get("/data", response_model=ApiResponse)
def get_ticket_data(ticket_type: str = "Camera MKN"):
    tt = ticket_type.lower().strip()
    if "playback" in tt:
        target_sheet = gsheet_sync.SHEET_NO_DATA
    elif "cứng" in tt or "hdd" in tt:
        target_sheet = gsheet_sync.SHEET_HDD
    elif "đầu ghi" in tt or "dvr" in tt:
        target_sheet = gsheet_sync.SHEET_DVR
    else:
        target_sheet = gsheet_sync.SHEET_CAM_MKN
        
    try:
        ok, df = gsheet_sync.read_ticket_sheet(target_sheet)
        if not ok:
            # Clear cache for this type if it failed
            if ticket_type in TICKET_CACHE:
                del TICKET_CACHE[ticket_type]
            return ApiResponse(success=False, status="error", message=str(df))
            
        df = normalize_ticket_df(df)
        records = df.to_dict('records')
        TICKET_CACHE[ticket_type] = records
        return ApiResponse(success=True, status="ok", data=records)
    except Exception as e:
        return ApiResponse(success=False, status="error", message=str(e))


@router.post("/jobs", response_model=ApiResponse)
async def create_ticket_job(
    file: Optional[UploadFile] = File(None),
    ticket_type: str = Form("Camera MKN") # Default from UI
):
    global GLOBAL_TICKET_DRIVER
    job_id = str(uuid.uuid4())
    
    # Check concurrent jobs (we only allow 1 Selenium job at a time to prevent conflicts)
    for j_id, j_data in JOB_STORE.items():
        if j_data["status"] == "running":
            raise HTTPException(status_code=409, detail="A Ticket job is already running. Please wait.")

    is_gsheet_mode = False
    if file:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".csv" if file.filename.endswith(".csv") else ".xlsx")
        os.close(tmp_fd)
        with open(tmp_path, "wb") as buffer:
            buffer.write(await file.read())
        try:
            if tmp_path.endswith(".csv"):
                try: df_in = pd.read_csv(tmp_path, encoding='utf-8-sig')
                except: df_in = pd.read_csv(tmp_path, encoding='cp1252')
            else:
                df_in = pd.read_excel(tmp_path)
            df_in = normalize_ticket_df(df_in)
            data_list = df_in.to_dict('records')
        except Exception as e:
            if os.path.exists(tmp_path): os.remove(tmp_path)
            raise HTTPException(status_code=400, detail=f"Lỗi đọc file: {e}")
        if os.path.exists(tmp_path): os.remove(tmp_path)
    else:
        if ticket_type not in TICKET_CACHE or not TICKET_CACHE[ticket_type]:
            raise HTTPException(status_code=400, detail=f"Dữ liệu cho {ticket_type} chưa được tải từ GSheet hoặc đang trống.")
        data_list = TICKET_CACHE[ticket_type]
        is_gsheet_mode = True

    sys_mode = "VCC"
    func_name = "Camera"
    is_dvr = False
    is_no_data = False
    is_hdd = False
    
    tt = ticket_type.lower().strip()
    if "đầu ghi" in tt or "dvr" in tt:
        is_dvr = True
    elif "playback" in tt:
        is_no_data = True
    elif "cứng" in tt or "hdd" in tt:
        is_hdd = True
    # Instantiate existing PyQt5 QThread Worker
    worker = TicketScanner(
        driver=GLOBAL_TICKET_DRIVER,
        data_list=data_list,
        sys_mode=sys_mode,
        func_name=func_name,
        is_gsheet_mode=is_gsheet_mode,
        is_dvr=is_dvr,
        is_no_data=is_no_data,
        is_hdd=is_hdd
    )
    
    JOB_STORE[job_id] = {
        "success": True,
        "status": "running", # "queued", "running", "completed", "failed", "cancelled"
        "job_id": job_id,
        "message": None,
        "progress": 0,
        "total": len(data_list),
        "results": [],
        "logs": [],
        "output_file": {"available": False, "filename": None},
        "error": None,
        "_worker": worker,
        "_data_list": data_list 
    }
    
    def on_log(msg):
        if job_id in JOB_STORE:
            JOB_STORE[job_id]["logs"].append({"msg": msg})
            
    def on_driver(driver):
        global GLOBAL_TICKET_DRIVER
        GLOBAL_TICKET_DRIVER = driver
        
    def on_finished(result: dict = None):
        if job_id in JOB_STORE:
            if result and not result.get("success", True):
                JOB_STORE[job_id]["status"] = "failed"
            elif JOB_STORE[job_id]["status"] == "running":
                JOB_STORE[job_id]["status"] = "completed"
            
            if result:
                JOB_STORE[job_id]["success"] = result.get("success", True)
                if "output_file" in result:
                    JOB_STORE[job_id]["output_file"] = result["output_file"]
                if "message" in result:
                    JOB_STORE[job_id]["message"] = result["message"]
                    JOB_STORE[job_id]["logs"].append({"msg": result["message"]})
                    
            if "_data_list" in JOB_STORE[job_id]:
                JOB_STORE[job_id]["results"] = JOB_STORE[job_id]["_data_list"]
                
    worker.on_log = on_log
    worker.on_driver = on_driver
    worker.on_finished = on_finished
    
    def thread_target():
        try:
            worker.run()
        except Exception as e:
            if job_id in JOB_STORE:
                JOB_STORE[job_id]["status"] = "failed"
                JOB_STORE[job_id]["success"] = False
                JOB_STORE[job_id]["error"] = {"code": "RUNTIME_ERROR", "message": str(e)}
                import traceback
                JOB_STORE[job_id]["logs"].append({"msg": f"Lỗi Runtime: {e}\n{traceback.format_exc()}"})
        finally:
            if job_id in JOB_STORE:
                # To avoid memory leak with Qt signals
                JOB_STORE[job_id].pop("_worker", None)
                JOB_STORE[job_id].pop("_data_list", None)

    import threading
    threading.Thread(target=thread_target, daemon=True).start()
    
    return ApiResponse(success=True, status="ok", data={"job_id": job_id})

@router.post("/jobs/check-status", response_model=ApiResponse)
async def create_check_ticket_job(
    file: Optional[UploadFile] = File(None),
    ticket_type: str = Form("Camera MKN")
):
    global GLOBAL_TICKET_DRIVER
    if not CheckTicketScanner:
        raise HTTPException(status_code=500, detail="CheckTicketScanner module not found")
        
    job_id = str(uuid.uuid4())
    for j_id, j_data in JOB_STORE.items():
        if j_data["status"] == "running":
            raise HTTPException(status_code=409, detail="A Ticket job is already running. Please wait.")

    if ticket_type == "ALL":
        # ============================================================
        # BACKEND ORCHESTRATION LAYER FOR "ALL" TICKETS
        # Runs CheckTicketScanner sequentially for each ticket type.
        # Uses local DataFrames (NOT global TICKET_CACHE) to prevent
        # race conditions from cache overwrites.
        # ============================================================
        JOB_STORE[job_id] = {
            "success": True,
            "status": "running",
            "job_id": job_id,
            "message": "Bắt đầu kiểm tra tất cả Ticket...",
            "progress": 0,
            "total": 0,
            "results": {},
            "logs": [{"msg": "Khởi tạo tiến trình CHECK TẤT CẢ TICKET..."}],
            "output_file": {"available": False, "filename": None},
            "error": None,
            "current_type": None,
            "completed_types": [],
            "_workers": [],
            "_orchestrator_running": True
        }

        def orchestrator_thread():
            global GLOBAL_TICKET_DRIVER
            import traceback
            from app.services import gsheet_sync
            import pandas as pd

            types_to_run = ["Camera MKN", "Lỗi Đầu ghi", "Cam không có playback", "Lỗi ổ cứng"]
            all_dfs = {}
            total_records = 0

            # ── PHASE 1: Pre-load ALL datasets into local variables ──
            # This avoids the global TICKET_CACHE overwrite race condition.
            for t in types_to_run:
                if not JOB_STORE.get(job_id, {}).get("_orchestrator_running", False):
                    JOB_STORE[job_id]["status"] = "cancelled"
                    JOB_STORE[job_id]["logs"].append({"msg": "Tiến trình bị hủy trước khi tải xong dữ liệu."})
                    return
                try:
                    JOB_STORE[job_id]["logs"].append({"msg": f"📥 Đang tải dữ liệu: {t}..."})

                    # Resolve sheet name using gsheet_sync constants
                    tt_lower = t.lower().strip()
                    if "playback" in tt_lower:
                        target_sheet = gsheet_sync.SHEET_NO_DATA
                    elif "cứng" in tt_lower or "hdd" in tt_lower:
                        target_sheet = gsheet_sync.SHEET_HDD
                    elif "đầu ghi" in tt_lower or "dvr" in tt_lower:
                        target_sheet = gsheet_sync.SHEET_DVR
                    else:
                        target_sheet = gsheet_sync.SHEET_CAM_MKN

                    ok, df = gsheet_sync.read_ticket_sheet(target_sheet)
                    if not ok:
                        if "Sheet trong hoac khong co du lieu" in str(df) or "Sheet trống" in str(df):
                            JOB_STORE[job_id]["logs"].append({"msg": f"[WARN] Bỏ qua {t}: Sheet hiện đang trống (Không có ticket nào cần xử lý)."})
                            # Provide empty dataframe to prevent KeyError down the line
                            import pandas as pd
                            df = pd.DataFrame(columns=["Vùng", "Tên shop", "Mã shop", "Ticket"])
                        else:
                            raise Exception(f"Không thể đọc sheet '{target_sheet}': {df}")

                    df = normalize_ticket_df(df)
                    all_dfs[t] = df
                    total_records += len(df)
                    JOB_STORE[job_id]["results"][t] = []
                    JOB_STORE[job_id]["logs"].append({"msg": f"[SUCCESS] {t}: {len(df)} dòng dữ liệu"})
                except Exception as e:
                    JOB_STORE[job_id]["status"] = "failed"
                    JOB_STORE[job_id]["success"] = False
                    JOB_STORE[job_id]["error"] = {"code": "DATA_LOAD_ERROR", "message": f"Lỗi tải dữ liệu {t}: {str(e)}"}
                    JOB_STORE[job_id]["logs"].append({"msg": f"[FAIL] Lỗi Data: {str(e)}"})
                    JOB_STORE[job_id].pop("_orchestrator_running", None)
                    JOB_STORE[job_id].pop("_workers", None)
                    return

            JOB_STORE[job_id]["total"] = total_records
            JOB_STORE[job_id]["logs"].append({"msg": f"📊 Tổng cộng: {total_records} dòng cần kiểm tra"})

            # ── PHASE 2: Run CheckTicketScanner SEQUENTIALLY per type ──
            current_type_label = "N/A"
            _driver_ref = [GLOBAL_TICKET_DRIVER]  # Mutable container for driver passthrough
            try:
                for type_index, t in enumerate(types_to_run):
                    current_type_label = t
                    JOB_STORE[job_id]["current_type"] = t

                    # Check cancel before starting each type
                    if not JOB_STORE.get(job_id, {}).get("_orchestrator_running", False):
                        JOB_STORE[job_id]["status"] = "cancelled"
                        JOB_STORE[job_id]["logs"].append({"msg": f"⏹ Tiến trình bị hủy trước khi bắt đầu {t}."})
                        break

                    JOB_STORE[job_id]["logs"].append({"msg": f"═══ [{type_index+1}/4] BẮT ĐẦU KIỂM TRA: {t} ═══"})

                    df = all_dfs[t]
                    if len(df) == 0:
                        JOB_STORE[job_id]["logs"].append({"msg": f"[WARN] {t} không có dữ liệu. Bỏ qua."})
                        continue

                    tt_lower = t.lower().strip()
                    is_dvr = ("đầu ghi" in tt_lower or "dvr" in tt_lower)
                    is_no_data = ("playback" in tt_lower)
                    is_hdd = ("cứng" in tt_lower or "hdd" in tt_lower)

                    # Pass the CURRENT driver (possibly updated by previous scanner)
                    # so the scanner can reuse the Azure AD session.
                    worker = CheckTicketScanner(
                        file_path=None,
                        dataframe=df,
                        driver=_driver_ref[0],
                        is_dvr=is_dvr,
                        is_no_data=is_no_data,
                        is_hdd=is_hdd
                    )
                    JOB_STORE[job_id]["_workers"].append(worker)

                    # ── Closure-safe callbacks ──
                    # Use default argument binding to capture current values
                    # of 't' and 'worker_progress' at definition time,
                    # preventing the classic Python late-binding closure bug.
                    _wp = {"val": 0}

                    def make_on_log(type_name):
                        def on_log(msg):
                            if job_id in JOB_STORE:
                                JOB_STORE[job_id]["logs"].append({"msg": f"[{type_name}] {msg}"})
                        return on_log

                    def make_on_progress(wp_ref):
                        def on_progress(c, tot):
                            if job_id in JOB_STORE:
                                diff = c - wp_ref["val"]
                                if diff > 0:
                                    JOB_STORE[job_id]["progress"] += diff
                                    wp_ref["val"] = c
                        return on_progress

                    worker_result = [None]

                    def make_on_finished(wr_ref):
                        def on_finished(result):
                            wr_ref[0] = result
                        return on_finished

                    def on_driver_capture(driver):
                        # Update module-level global via the orchestrator_thread's
                        # 'global GLOBAL_TICKET_DRIVER' declaration (line 211).
                        # We access it directly — Python closures can read/write
                        # globals declared in an enclosing function.
                        _driver_ref[0] = driver

                    worker.on_log = make_on_log(t)
                    worker.on_progress = make_on_progress(_wp)
                    worker.on_finished = make_on_finished(worker_result)
                    worker.on_driver = on_driver_capture

                    # Run scanner synchronously (blocks until this type is done)
                    worker.run()

                    # Propagate any driver update back to the module-level global
                    GLOBAL_TICKET_DRIVER = _driver_ref[0]

                    # Capture result DataFrame if available
                    if hasattr(worker, 'dataframe') and worker.dataframe is not None:
                        try:
                            JOB_STORE[job_id]["results"][t] = worker.dataframe.to_dict('records')
                        except Exception:
                            pass

                    # Check scanner result for failure
                    res = worker_result[0]
                    if res and not res.get("success", True):
                        err_msg = res.get("message", "Scanner failed without message.")
                        raise Exception(f"{t}: {err_msg}")

                    JOB_STORE[job_id]["logs"].append({"msg": f"[SUCCESS] [{type_index+1}/4] HOÀN TẤT: {t}"})

            except Exception as e:
                JOB_STORE[job_id]["status"] = "failed"
                JOB_STORE[job_id]["success"] = False
                JOB_STORE[job_id]["error"] = {"code": "RUNTIME_ERROR", "message": f"Lỗi khi xử lý {current_type_label}: {str(e)}"}
                JOB_STORE[job_id]["logs"].append({"msg": f"[FAIL] Lỗi Runtime tại {current_type_label}: {e}\n{traceback.format_exc()}"})
            else:
                if JOB_STORE.get(job_id, {}).get("_orchestrator_running", False):
                    JOB_STORE[job_id]["status"] = "completed"
                    JOB_STORE[job_id]["success"] = True
                    JOB_STORE[job_id]["message"] = "Đã kiểm tra xong TẤT CẢ Ticket."
                    JOB_STORE[job_id]["logs"].append({"msg": "🎉 Đã hoàn tất kiểm tra tất cả 4 loại Ticket."})
            finally:
                if job_id in JOB_STORE:
                    JOB_STORE[job_id].pop("_workers", None)
                    JOB_STORE[job_id].pop("_orchestrator_running", None)

        import threading
        threading.Thread(target=orchestrator_thread, daemon=True).start()
        return ApiResponse(success=True, status="ok", data={"job_id": job_id})

    # ORIGINAL SINGLE TYPE
    file_path = None
    if file:
        from app.paths import RUNTIME_DIR
        import os
        OUTPUT_DIR = RUNTIME_DIR / "outputs"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        file_path = os.path.join(OUTPUT_DIR, f"{job_id}_{file.filename}")
        with open(file_path, "wb") as buffer: buffer.write(await file.read())
        try:
            if file_path.endswith(".csv"):
                try: df = pd.read_csv(file_path, encoding='utf-8-sig')
                except: df = pd.read_csv(file_path, encoding='cp1252')
            else:
                df = pd.read_excel(file_path)
            df = normalize_ticket_df(df)
        except Exception as e:
            if os.path.exists(file_path): os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Lỗi đọc file: {e}")
    else:
        if ticket_type not in TICKET_CACHE or not TICKET_CACHE[ticket_type]:
            raise HTTPException(status_code=400, detail=f"Dữ liệu cho {ticket_type} chưa được tải từ GSheet hoặc đang trống.")
        df = pd.DataFrame(TICKET_CACHE[ticket_type])

    tt = ticket_type.lower().strip()
    is_dvr = ("đầu ghi" in tt or "dvr" in tt)
    is_no_data = ("playback" in tt)
    is_hdd = ("cứng" in tt or "hdd" in tt)
    worker = CheckTicketScanner(
        file_path=file_path,
        dataframe=df,
        driver=GLOBAL_TICKET_DRIVER,
        is_dvr=is_dvr,
        is_no_data=is_no_data,
        is_hdd=is_hdd
    )
    
    JOB_STORE[job_id] = {
        "success": True,
        "status": "running",
        "job_id": job_id,
        "message": None,
        "progress": 0,
        "total": len(df),
        "results": [],
        "logs": [],
        "output_file": {"available": False, "filename": None},
        "error": None,
        "_worker": worker,
        "_data_list": df.to_dict('records') if hasattr(df, 'to_dict') else []
    }
    
    def on_log(msg):
        if job_id in JOB_STORE: JOB_STORE[job_id]["logs"].append({"msg": msg})
    def on_progress(c, t):
        if job_id in JOB_STORE:
            JOB_STORE[job_id]["progress"] = c
            JOB_STORE[job_id]["total"] = t
    def on_driver(driver):
        global GLOBAL_TICKET_DRIVER
        GLOBAL_TICKET_DRIVER = driver
    def on_finished(result):
        if job_id in JOB_STORE:
            if result and not result.get("success", True):
                JOB_STORE[job_id]["status"] = "failed"
            elif JOB_STORE[job_id]["status"] == "running":
                JOB_STORE[job_id]["status"] = "completed"
            if result:
                JOB_STORE[job_id]["success"] = result.get("success", True)
                if "output_file" in result:
                    JOB_STORE[job_id]["output_file"] = result["output_file"]
                if "message" in result:
                    JOB_STORE[job_id]["message"] = result["message"]
                    JOB_STORE[job_id]["logs"].append({"msg": result["message"]})
                    
            if "_data_list" in JOB_STORE[job_id]:
                JOB_STORE[job_id]["results"] = JOB_STORE[job_id]["_data_list"]
                
    worker.on_log = on_log
    worker.on_driver = on_driver
    worker.on_progress = on_progress
    worker.on_finished = on_finished
    
    def thread_target():
        try:
            worker.run()
        except Exception as e:
            if job_id in JOB_STORE:
                JOB_STORE[job_id]["status"] = "failed"
                JOB_STORE[job_id]["success"] = False
                JOB_STORE[job_id]["error"] = {"code": "RUNTIME_ERROR", "message": str(e)}
                import traceback
                JOB_STORE[job_id]["logs"].append({"msg": f"Lỗi Runtime: {e}\n{traceback.format_exc()}"})
        finally:
            if job_id in JOB_STORE:
                JOB_STORE[job_id].pop("_worker", None)
                JOB_STORE[job_id].pop("_data_list", None)

    import threading
    threading.Thread(target=thread_target, daemon=True).start()
    return ApiResponse(success=True, status="ok", data={"job_id": job_id})

@router.get("/jobs/{job_id}", response_model=ApiResponse)
async def get_ticket_job(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
        
    data = JOB_STORE[job_id].copy()
    # Pop ALL private/non-serializable fields before returning to Pydantic
    data.pop("_worker", None)
    data.pop("_workers", None)
    data.pop("_data_list", None)
    data.pop("_orchestrator_running", None)
    
    return ApiResponse(success=True, status="ok", data=data)

@router.post("/jobs/{job_id}/cancel", response_model=ApiResponse)
async def cancel_ticket_job(job_id: str):
    if job_id in JOB_STORE and JOB_STORE[job_id]["status"] == "running":
        worker = JOB_STORE[job_id].get("_worker")
        if worker and hasattr(worker, 'stop'):
            worker.stop()
            
        if "_orchestrator_running" in JOB_STORE[job_id]:
            JOB_STORE[job_id]["_orchestrator_running"] = False
        if "_workers" in JOB_STORE[job_id]:
            for w in JOB_STORE[job_id]["_workers"]:
                if hasattr(w, 'stop'):
                    w.stop()
                    
        JOB_STORE[job_id]["status"] = "cancelled"
    return ApiResponse(success=True, status="ok", message="Cancel signal sent")


from fastapi.responses import FileResponse
import re

@router.get("/download/{job_id}", response_class=FileResponse)
async def download_ticket_job_result(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = JOB_STORE[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job chưa hoàn thành. Không thể tải file.")
        
    output_meta = job.get("output_file")
    if not output_meta or not output_meta.get("available"):
        raise HTTPException(status_code=400, detail="Không có file kết quả để tải.")
        
    filename = output_meta.get("filename")
    if not filename:
        raise HTTPException(status_code=404, detail="Tên file không hợp lệ.")
        
    # Security: Path traversal validation
    if re.search(r"[\/\\]", filename) or ".." in filename:
        raise HTTPException(status_code=400, detail="Filename không hợp lệ (Path Traversal detected).")
        
    from app.paths import RUNTIME_DIR
    import os
    OUTPUT_DIR = RUNTIME_DIR / "outputs"
    file_path = os.path.join(OUTPUT_DIR, filename)
    
    # Double check security
    resolved_path = os.path.realpath(file_path)
    if not resolved_path.startswith(os.path.realpath(str(OUTPUT_DIR))):
        raise HTTPException(status_code=403, detail="File path is outside allowed directory.")
        
    if not os.path.exists(resolved_path):
        raise HTTPException(status_code=404, detail="File kết quả không tồn tại trên hệ thống.")
        
    return FileResponse(path=resolved_path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
