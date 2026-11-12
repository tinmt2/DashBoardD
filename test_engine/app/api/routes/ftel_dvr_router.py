import os
import time
import uuid
import threading
import pandas as pd
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services import gsheet_sync
from app.services.logging_utils import get_logger, session_id_var, action_id_var, job_id_var
from app.services.logging_utils import get_logger, session_id_var, action_id_var, job_id_var
logger = get_logger(__name__)
from app.services import browser_manager, backend_check
from app.services.ftel_dvr_service import FtelDvrScanner
from app.api.schemas.common import ApiResponse

router = APIRouter(prefix="/api/ftel-dvr", tags=["ftel-dvr"])

class DvrItem(BaseModel):
    index: int
    ma_shop: str
    ten_shop: str
    vung: str
    ip: str
    status: str
    cam_status: str
    cam_online: int
    cam_total: int
    latency: str
    password: str

# Stores global state
JOB_STORE: Dict[str, Any] = {}
FTEL_STATE: Dict[str, Any] = {
    "status": "idle",
    "progress": 0,
    "total": 0,
    "results": [],
    "error": None,
    "worker": None,
    "df_cache": None
}

def df_to_results(df: pd.DataFrame) -> List[Dict]:
    results = []
    for idx, row in df.iterrows():
        existing_pwd = ""
        if len(row) > 7:
            existing_pwd = str(row.iloc[7]).strip()
        elif "Ticket add cam counting" in row:
            existing_pwd = str(row["Ticket add cam counting"]).strip()
        elif "Mật khẩu" in row:
            existing_pwd = str(row["Mật khẩu"]).strip()
            
        if existing_pwd.lower() in ["nan", "none", "sai pass", "-", ""]:
            existing_pwd = ""
            
        results.append({
            "index": idx,
            "ma_shop": str(row.get("Mã shop", "")).strip().removesuffix(".0"),
            "ten_shop": str(row.get("Tên shop", "")).strip(),
            "vung": str(row.get("Vùng", "")).strip(),
            "ip": str(row.get("IP", "")).strip(),
            "status": "Chưa check",
            "cam_status": "-",
            "cam_online": 0,
            "cam_total": 0,
            "latency": "",
            "password": existing_pwd,
            "existing_password": existing_pwd
        })
    return results

@router.get("/data", response_model=ApiResponse)
async def get_ftel_data(refresh: bool = False):
    if FTEL_STATE["df_cache"] is None or refresh:
        try:
            ok, df = gsheet_sync.read_ticket_sheet('Đầu ghi Ftel')
            if not ok:
                return ApiResponse(success=False, status="error", message="Không thể tải sheet: " + str(df))
            FTEL_STATE["df_cache"] = df
        except Exception as e:
            return ApiResponse(success=False, status="error", message=str(e))
            
    res = df_to_results(FTEL_STATE["df_cache"])
    FTEL_STATE["results"] = res
    return ApiResponse(success=True, status="ok", data=res)

@router.get("/status", response_model=ApiResponse)
async def get_ftel_status():
    return ApiResponse(success=True, status="ok", data={
        "status": FTEL_STATE["status"],
        "progress": FTEL_STATE["progress"],
        "total": FTEL_STATE["total"],
        "results": FTEL_STATE["results"],
        "error": FTEL_STATE["error"]
    })

def background_scan():
    FTEL_STATE["status"] = "running"
    
    # Pre-populate results
    res_list = df_to_results(FTEL_STATE["df_cache"])
    FTEL_STATE["results"] = res_list
    worker = FtelDvrScanner(FTEL_STATE["df_cache"])
    FTEL_STATE["worker"] = worker
    FTEL_STATE["total"] = len(FTEL_STATE["df_cache"])
    FTEL_STATE["progress"] = 0
    
    def on_row_checked(idx, st, cs, cd, lat, pwd, co, ct):
        if 0 <= idx < len(FTEL_STATE["results"]):
            FTEL_STATE["results"][idx]["status"] = st
            FTEL_STATE["results"][idx]["cam_status"] = cs
            FTEL_STATE["results"][idx]["latency"] = lat
            FTEL_STATE["results"][idx]["password"] = pwd
            FTEL_STATE["results"][idx]["cam_online"] = co
            FTEL_STATE["results"][idx]["cam_total"] = ct
            FTEL_STATE["results"][idx]["cam_details"] = cd
            
    def on_progress(c, t):
        FTEL_STATE["progress"] = c
        
    worker.on_row_checked = on_row_checked
    worker.on_progress = on_progress
    
    try:
        worker.run() # Synchronous run in current thread
        if not backend_check.GLOBAL_STOP and worker.is_running:
            FTEL_STATE["status"] = "completed"
        else:
            FTEL_STATE["status"] = "cancelled"
    except Exception as e:
        FTEL_STATE["status"] = "failed"
        FTEL_STATE["error"] = str(e)
    finally:
        FTEL_STATE["worker"] = None
        backend_check.GLOBAL_STOP = False

@router.post("/scan/start", response_model=ApiResponse)
async def start_ftel_scan():
    if FTEL_STATE["status"] == "running":
        return ApiResponse(success=False, status="error", message="Already running")
    if FTEL_STATE["df_cache"] is None:
        return ApiResponse(success=False, status="error", message="Please load data first")
        
    backend_check.GLOBAL_STOP = False
    t = threading.Thread(target=background_scan, daemon=True)
    t.start()
    return ApiResponse(success=True, status="ok")

@router.post("/scan/stop", response_model=ApiResponse)
async def stop_ftel_scan():
    if FTEL_STATE["worker"]:
        FTEL_STATE["worker"].stop()
    backend_check.GLOBAL_STOP = True
    FTEL_STATE["status"] = "cancelled"
    return ApiResponse(success=True, status="ok")

@router.post("/auto-login", response_model=ApiResponse)
async def auto_login(data: dict):
    print("[FTEL-AUTOLOGIN-TRACE] router entered")
    
    ip = data.get("ip")
    port = data.get("port", 81)
    username = data.get("username", "admin")
    password = data.get("password", "")
    
    if password == "Sai Pass" or password == "Lỗi Form Web":
        password = ""
        
    print(f"IP: {ip}, Port: {port}, Password_present: {bool(password)}")
    
    if not ip:
        return ApiResponse(success=False, status="error", message="Thiếu IP")
        
    def run_browser():
        print("[FTEL-AUTOLOGIN-TRACE] thread start")
        try:
            from app.services import browser_manager
            import time
            from selenium.webdriver.common.by import By
            
            if FTEL_STATE.get("worker") is None:
                browser_manager.cleanup_chrome_sessions()
            
            driver = browser_manager.create_chrome_driver(detach=True, incognito=False, isolated_profile=True)
            print("[FTEL-AUTOLOGIN-TRACE] driver created")
            
            driver.get(f"http://{ip}:{port}")
            print("[FTEL-AUTOLOGIN-TRACE] driver.get() thành công")
            
            from app.services.ftel_dvr_service import PASSWORDS
            pwd_to_fill = password if password else PASSWORDS[0]
            
            def find_login_elements(ctx):
                u, p, b = None, None, None
                for sel in ["#login_userName_input", "#userName", "#username", "input[name='username']", "input[type='text']"]:
                    try:
                        els = ctx.find_elements(By.CSS_SELECTOR, sel)
                        for el in els:
                            if el.is_displayed() and el.is_enabled():
                                u = el; break
                        if u: break
                    except: pass
                for sel in ["#loginPsw", "#login_user_input", "#password", "#login_password", "input[type='password']"]:
                    try:
                        els = ctx.find_elements(By.CSS_SELECTOR, sel)
                        for el in els:
                            if el.is_displayed() and el.is_enabled():
                                p = el; break
                        if p: break
                    except: pass
                for sel in ["#loginBtn", ".loginBtnNormal", "#login_btn_user_ok", "button[type='submit']", ".btn-login", "#btnLogin", "button", "input[type='button']"]:
                    try:
                        els = ctx.find_elements(By.CSS_SELECTOR, sel)
                        for el in els:
                            if el.is_displayed() and el.is_enabled():
                                if "login" in el.get_attribute("class").lower() or "login" in el.get_attribute("id").lower() or "ok" in el.get_attribute("id").lower() or "đăng nhập" in el.text.lower() or "login" in el.text.lower():
                                    b = el; break
                        if b: break
                    except: pass
                if not b:
                    try:
                        els = ctx.find_elements(By.CSS_SELECTOR, "button, input[type='button'], div[id*='loginBtn'], div[id*='login']")
                        for el in els:
                            if el.is_displayed() and el.is_enabled():
                                b = el; break
                    except: pass
                return u, p, b

            user_el, pass_el, btn_el = None, None, None
            
            try:
                for _ in range(8):
                    user_el, pass_el, btn_el = find_login_elements(driver)
                    if user_el and pass_el:
                        print("[FTEL-AUTOLOGIN] login form detected")
                        break
                    time.sleep(1.5)
                    
                if not user_el or not pass_el:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        try:
                            driver.switch_to.frame(iframe)
                            user_el, pass_el, btn_el = find_login_elements(driver)
                            if user_el and pass_el:
                                print("[FTEL-AUTOLOGIN] login form detected (in iframe)")
                                break
                            driver.switch_to.default_content()
                        except:
                            driver.switch_to.default_content()
                            
                try:
                    has_gdevice = driver.execute_script("return typeof window.gDevice !== 'undefined' && window.gDevice !== null;")
                    if has_gdevice:
                        print("[FTEL-AUTOLOGIN] gDevice detected")
                    else:
                        print("[FTEL-AUTOLOGIN] gDevice NOT detected")
                        return
                except Exception as ge:
                    print("[FTEL-AUTOLOGIN] gDevice NOT detected")
                    return

            except Exception as wait_exc:
                print(f"[FTEL-AUTOLOGIN] Lỗi khi chờ form: {wait_exc}")
                return
            
            if user_el and pass_el:
                try:
                    user_el.clear()
                    user_el.send_keys(username)
                    pass_el.clear()
                    pass_el.send_keys(pwd_to_fill)
                except Exception:
                    try:
                        driver.execute_script('''
                            arguments[0].removeAttribute('readonly');
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                            arguments[2].value = arguments[3];
                            arguments[2].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[2].dispatchEvent(new Event('change', { bubbles: true }));
                        ''', user_el, username, pass_el, pwd_to_fill)
                    except: pass
                
                print("[FTEL-AUTOLOGIN] login submitted")
                
                if btn_el:
                    time.sleep(0.5)
                    try:
                        btn_el.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", btn_el)
                        except: pass
            else:
                print("[FTEL-AUTOLOGIN] Không tìm thấy form đăng nhập.")
                
        except Exception as e:
            import traceback
            print(f"[FTEL-AUTOLOGIN-TRACE] exception: {traceback.format_exc()}")

    print("[FTEL-AUTOLOGIN-TRACE] thread created")
    t = threading.Thread(target=run_browser, daemon=True)
    t.start()
    return ApiResponse(success=True, status="ok", message="Chrome started")

    print("[FTEL-AUTOLOGIN-TRACE] router entered")
    
    ip = data.get("ip")
    port = data.get("port", 81)
    username = data.get("username", "admin")
    password = data.get("password", "")
    if password == "Sai Pass": password = ""
    if password == "Lỗi Form Web": password = ""
    
    print(f"IP: {ip}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print(f"Password_present: {bool(password)}")
    
    if not ip:
        return ApiResponse(success=False, status="error", message="Thiếu IP")
        
    def run_browser():
        print("[FTEL-AUTOLOGIN-TRACE] thread start")
        print("[FTEL-AUTOLOGIN-TRACE] open_browser_for_dvr ENTER")
        try:
            print("[FTEL-AUTOLOGIN-TRACE] ENTER run_browser")
            
            if FTEL_STATE.get("worker") is None:
                browser_manager.cleanup_chrome_sessions()
            
            print("[FTEL-AUTOLOGIN-TRACE] create Chrome options (via browser_manager)")
            print("[FTEL-AUTOLOGIN-TRACE] create Chrome Service (via browser_manager)")
            print("[FTEL-AUTOLOGIN-TRACE] create webdriver.Chrome() (via browser_manager)")
            
            try:
                driver = browser_manager.create_chrome_driver(detach=True, incognito=False, isolated_profile=True)
                print("[FTEL-AUTOLOGIN-TRACE] driver created")
            except Exception as d_err:
                import traceback
                print(f"[FTEL-AUTOLOGIN-TRACE] STEP: Create Driver")
                print(f"[FTEL-AUTOLOGIN-TRACE] exception type: {type(d_err).__name__}")
                print(f"[FTEL-AUTOLOGIN-TRACE] exception message: {str(d_err)}")
                print(f"[FTEL-AUTOLOGIN-TRACE] traceback: {traceback.format_exc()}")
                return
            
            print("[FTEL-AUTOLOGIN-TRACE] driver.get(URL) Started")
            try:
                driver.get(f"http://{ip}:{port}")
            except Exception as g_err:
                import traceback
                print(f"[FTEL-AUTOLOGIN-TRACE] STEP: driver.get()")
                print(f"[FTEL-AUTOLOGIN-TRACE] exception type: {type(g_err).__name__}")
                print(f"[FTEL-AUTOLOGIN-TRACE] exception message: {str(g_err)}")
                print(f"[FTEL-AUTOLOGIN-TRACE] traceback: {traceback.format_exc()}")
                return
            
            print("[FTEL-AUTOLOGIN-TRACE] driver.get() thành công")
                        
        except Exception as e:
            import traceback
            print(f"[FTEL-AUTOLOGIN-TRACE] exception type: {type(e).__name__}")
            print(f"[FTEL-AUTOLOGIN-TRACE] exception message: {str(e)}")
            print(f"[FTEL-AUTOLOGIN-TRACE] traceback: {traceback.format_exc()}")

    print("[FTEL-AUTOLOGIN-TRACE] thread created")
    t = threading.Thread(target=run_browser, daemon=True)
    t.start()
    return ApiResponse(success=True, status="ok", message="Chrome started")

    ip = data.get("ip")
    port = data.get("port", 81)
    password = data.get("password", "")
    if password == "Sai Pass": password = ""
    if password == "Lỗi Form Web": password = ""
    
    if not ip:
        return ApiResponse(success=False, status="error", message="Thiếu IP")
        
    def run_browser():
        try:
            if FTEL_STATE["worker"] is None: # Not scanning
                browser_manager.cleanup_chrome_sessions()
            driver = browser_manager.create_chrome_driver(detach=True, incognito=False)
            driver.get(f"http://{ip}:{port}")
            
            from selenium.webdriver.common.by import By
            import time
            username = "admin"
            from app.services.ftel_dvr_service import PASSWORDS
            pwd_to_fill = password if password else PASSWORDS[0] if password else ""
                
            def find_login_elements(ctx):
                u, p, b = None, None, None
                for sel in ["#login_userName_input", "#userName", "#username", "input[name='username']", "input[type='text']"]:
                    try:
                        for el in ctx.find_elements(By.CSS_SELECTOR, sel):
                            if el.is_displayed() and el.is_enabled():
                                u = el; break
                        if u: break
                    except: pass
                for sel in ["#loginPsw", "#login_user_input", "#password", "#login_password", "input[type='password']"]:
                    try:
                        for el in ctx.find_elements(By.CSS_SELECTOR, sel):
                            if el.is_displayed() and el.is_enabled():
                                p = el; break
                        if p: break
                    except: pass
                for sel in ["#loginBtn", ".loginBtnNormal", "#login_btn_user_ok", "button[type='submit']", ".btn-login", "#btnLogin", "button", "input[type='button']"]:
                    try:
                        for el in ctx.find_elements(By.CSS_SELECTOR, sel):
                            if el.is_displayed() and el.is_enabled():
                                b = el; break
                        if b: break
                    except: pass
                if not b:
                    try:
                        for el in ctx.find_elements(By.CSS_SELECTOR, "button, input[type='button'], div[id*='login']"):
                            if el.is_displayed() and el.is_enabled():
                                b = el; break
                    except: pass
                return u, p, b
                
            user_el, pass_el, btn_el = None, None, None
            time.sleep(4)
            for _ in range(8):
                user_el, pass_el, btn_el = find_login_elements(driver)
                if user_el and pass_el: break
                time.sleep(1.5)
                
            if not user_el or not pass_el:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        user_el, pass_el, btn_el = find_login_elements(driver)
                        if user_el and pass_el: break
                        driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
                        
            if user_el and pass_el:
                try:
                    user_el.clear(); user_el.send_keys(username)
                    pass_el.clear(); pass_el.send_keys(pwd_to_fill)
                except:
                    try:
                        driver.execute_script("""
                            arguments[0].removeAttribute('readonly');
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                            arguments[2].value = arguments[3];
                            arguments[2].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[2].dispatchEvent(new Event('change', { bubbles: true }));
                        """, user_el, username, pass_el, pwd_to_fill)
                    except: pass
                if btn_el:
                    time.sleep(0.5)
                    try: btn_el.click()
                    except:
                        try: driver.execute_script("arguments[0].click();", btn_el)
                        except: pass
                        
        except Exception as e:
            pass

    threading.Thread(target=run_browser, daemon=True).start()
    return ApiResponse(success=True, status="ok", message="Chrome started")

from fastapi import File, Form, UploadFile
from typing import Optional
import tempfile
from app.services import check_cam_service

def dvr_worker_task(job_id: str, df: pd.DataFrame, session_id: str = None, action_id: str = None):
    if session_id: session_id_var.set(session_id)
    if action_id: action_id_var.set(action_id)
    job_id_var.set(job_id)
    logger.info(f'Job {job_id} started', extra={'event': 'JOB_STARTED', 'metadata': {'mode': 'dvr'}})
    JOB_STORE[job_id]["status"] = "running"
    backend_check.signal_start(job_id)
    try:
        # FtelDvrScanner takes df_data
        worker = FtelDvrScanner(df)
        JOB_STORE[job_id]["worker"] = worker
        JOB_STORE[job_id]["total"] = len(df)
        JOB_STORE[job_id]["progress"] = 0
        
        # Populate initial results
        res_list = df_to_results(df)
        JOB_STORE[job_id]["results"] = res_list
        
        def on_row_checked(idx, st, cs, cd, lat, pwd, co, ct):
            if 0 <= idx < len(JOB_STORE[job_id]["results"]):
                JOB_STORE[job_id]["results"][idx]["status"] = st
                JOB_STORE[job_id]["results"][idx]["cam_status"] = cs
                JOB_STORE[job_id]["results"][idx]["latency"] = lat
                JOB_STORE[job_id]["results"][idx]["password"] = pwd
                JOB_STORE[job_id]["results"][idx]["cam_online"] = co
                JOB_STORE[job_id]["results"][idx]["cam_total"] = ct
                JOB_STORE[job_id]["results"][idx]["cam_details"] = cd
                
        def on_progress(c, t):
            JOB_STORE[job_id]["progress"] = c
            if c % 50 == 0 or c == t: logger.info(f"Progress {c}/{t}", extra={"event": "JOB_PROGRESS", "metadata": {"processed": c, "total": t}})
            
        worker.on_row_checked = on_row_checked
        worker.on_progress = on_progress
        
        worker.run()
        
        if backend_check.is_stopped(job_id):
            logger.info(f"Job {job_id} cancelled", extra={"event": "JOB_CANCELLED"})
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

@router.post("/jobs", response_model=ApiResponse)
async def create_dvr_job(
    file: Optional[UploadFile] = File(None),
    vaccine: bool = Form(False),
    lc: bool = Form(False),
    mode: str = Form("monitor")
):
    job_id = str(uuid.uuid4())
    
    if file:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".csv" if file.filename.endswith(".csv") else ".xlsx")
        os.close(tmp_fd)
        with open(tmp_path, "wb") as buffer:
            buffer.write(await file.read())
        try:
            df_in = check_cam_service.read_input_file(tmp_path)
            filter_options = {"vaccine": vaccine, "lc": lc}
            df_process = check_cam_service.filter_shops(df_in, filter_options)
        except Exception as e:
            return ApiResponse(success=False, status="error", message=f"L?i d?c file: {e}")
        finally:
            try: os.remove(tmp_path)
            except: pass
    else:
        # Fallback to df_cache if no file
        if FTEL_STATE["df_cache"] is None:
            # Auto fetch from Google Sheets if not already cached
            from app.services import gsheet_sync
            ok, df = gsheet_sync.read_ticket_sheet("Đầu ghi Ftel")
            if not ok:
                return ApiResponse(success=False, status="error", message="Không thể tải sheet: " + str(df))
            FTEL_STATE["df_cache"] = df
        df_process = FTEL_STATE["df_cache"]

    JOB_STORE[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "total": 0,
        "results": [],
        "error": None,
        "worker": None,
        "mode": mode,
        "metrics": {"total_old_errors": 0, "new_errors": 0, "resolved": 0, "scanned": 0}
    }
    
    session_id = session_id_var.get()
    action_id = action_id_var.get()
    logger.info(f'Job {job_id} created', extra={'event': 'JOB_CREATED', 'metadata': {'mode': mode}})
    t = threading.Thread(target=dvr_worker_task, args=(job_id, df_process, session_id, action_id))
    t.start()
    
    return ApiResponse(success=True, status="ok", data={"job_id": job_id})

@router.get("/jobs/{job_id}", response_model=ApiResponse)
async def get_dvr_job(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
        
    data = JOB_STORE[job_id].copy()
    if "worker" in data: del data["worker"]
    
    # Calculate DVR metrics to match UI contract (Detected = new_errors + total_old_errors)
    # Actually FtelDvrScanner doesn't generate camera metric structure, so we simulate it or map it.
    err_count = sum(1 for r in data["results"] if r.get("status", "").lower() not in ["chua check", "ok"])
    data["metrics"] = {
        "total_old_errors": 0,
        "new_errors": err_count,
        "resolved": 0,
        "scanned": data["progress"],
        "online": data["progress"] - err_count,
        "offline": err_count
    }
    
    return ApiResponse(success=True, status="ok", data=data)

@router.post("/jobs/{job_id}/cancel", response_model=ApiResponse)
async def cancel_dvr_job(job_id: str):
    if job_id in JOB_STORE and JOB_STORE[job_id]["status"] in ["queued", "running"]:
        backend_check.signal_stop(job_id)
        if JOB_STORE[job_id]["worker"]:
            JOB_STORE[job_id]["worker"].stop()
        
        logger.info("DVR_JOB_STOP_REQUESTED", extra={"event": "DVR_JOB_STOP_REQUESTED", "metadata": {"job_id": job_id}})
    return ApiResponse(success=True, status="ok", message="Cancel signal sent")



@router.post("/jobs/{job_id}/export")
async def export_dvr_job(job_id: str):
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = JOB_STORE[job_id]
    # Filter out unprocessed results so partial exports work correctly
    results = [r for r in job.get("results", []) if r.get("status", "Chưa check") != "Chưa check"]
    if not results:
        raise HTTPException(status_code=400, detail="No partial data to export")
        
    expanded_rows = []
    for r in results:
        ma_shop = r.get("ma_shop", "")
        ten_shop = r.get("ten_shop", "")
        vung = r.get("vung", "")
        ip = r.get("ip", "")
        status = r.get("status", "")
        latency = r.get("latency", "")
        password = r.get("password", "")
        
        cam_details = r.get("cam_details", "")
        
        if not cam_details:
            cam_status_text = "DVR Offline" if status == "Offline" else "Lỗi kết nối DVR"
            expanded_rows.append({
                "Mã shop": ma_shop,
                "Tên shop": ten_shop,
                "Vùng": vung,
                "IP": ip,
                "Mã cam": "-",
                "Trạng thái cam": cam_status_text,
                "Trạng thái DVR": status,
                "Ping": latency,
                "Mật khẩu": password,
                "Ngày offline": "-"
            })
        else:
            try:
                import json
                cam_list = json.loads(cam_details)
                for cam in cam_list:
                    expanded_rows.append({
                        "Mã shop": ma_shop,
                        "Tên shop": ten_shop,
                        "Vùng": vung,
                        "IP": ip,
                        "Mã cam": cam.get("channel", "-"),
                        "Trạng thái cam": cam.get("status", "-"),
                        "Trạng thái DVR": status,
                        "Ping": latency,
                        "Mật khẩu": password,
                        "Ngày offline": cam.get("offline_date", "-")
                    })
            except Exception:
                # Fallback for old string format if any
                clines = cam_details.split("\n")
                for line in clines:
                    line = line.strip()
                    if not line: continue
                    parts = line.split(":", 1)
                    ma_cam = parts[0].strip() if len(parts) > 0 else "-"
                    trang_thai_cam = parts[1].strip() if len(parts) > 1 else "-"

                    expanded_rows.append({
                        "Mã shop": ma_shop,
                        "Tên shop": ten_shop,
                        "Vùng": vung,
                        "IP": ip,
                        "Mã cam": ma_cam,
                        "Trạng thái cam": trang_thai_cam,
                        "Trạng thái DVR": status,
                        "Ping": latency,
                        "Mật khẩu": password,
                        "Ngày offline": "-"
                    })
                
    df_export = pd.DataFrame(expanded_rows)
    
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(tmp_fd)
    
    try:
        df_export.to_excel(tmp_path, index=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return FileResponse(tmp_path, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename="dvr_ftel_export.xlsx")