import sys
import os
import time
import datetime
import pandas as pd
import requests
import json
import uuid
import platform
import subprocess
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from app.services import browser_manager
from app.paths import TOKEN_FILE as APP_TOKEN_FILE, CHROME_PROFILE_DIR, ensure_runtime_dirs

COT_TICKET_INDEX = 6  # Cột G (0-indexed: index 6) for 'Cam mkn'
URL_LOGIN = "https://ssc.fptshop.com.vn/s-pro/workflow/ticket/673769824183b58c119bd8cf"

class CheckTicketScanner:
# Output path
    
    def __init__(self, file_path=None, dataframe=None, driver=None, is_dvr=False, is_no_data=False, is_hdd=False):
        self.on_log = None
        self.on_progress = None
        self.on_finished = None
        self.file_path = file_path
        self.dataframe = dataframe
        self.is_running = True
        self.driver = driver
        self.is_dvr = is_dvr
        self.is_no_data = is_no_data
        self.is_hdd = is_hdd
        self.is_shared_driver = False
        self.is_driver_headless = False # Track if current driver is headless
        if driver: self.is_shared_driver = True

    def stop(self):
        self.is_running = False

    def get_token(self, driver):
        # ... (keep existing get_token logic)
        script_tim_token = """
        function findToken() {
            const storages = [localStorage, sessionStorage];
            for (let storage of storages) {
                for (let i = 0; i < storage.length; i++) {
                    let key = storage.key(i);
                    let value = storage.getItem(key);
                    if (!value) continue;
                    if (value.startsWith("eyJ") && value.length > 500) return value;
                    if (value.startsWith("Bearer eyJ")) return value.replace("Bearer ", "");
                    try {
                        let obj = JSON.parse(value);
                        if (obj.access_token) return obj.access_token;
                        if (obj.token) return obj.token;
                        if (obj.user && obj.user.access_token) return obj.user.access_token;
                    } catch(e) {}
                }
            }
            let cookies = document.cookie.split(';');
            for(let cookie of cookies) {
                let [name, val] = cookie.trim().split('=');
                if (val && val.startsWith("eyJ") && val.length > 500) return val;
            }
            return null;
        }
        return findToken();
        """
        try:
            return driver.execute_script(script_tim_token)
        except: return None

    def wait_for_login(self):
        if self.on_log: self.on_log("[WAIT] Đang đợi lấy Token từ Chrome...")
        
        # Auto-click Azure button once if possible
        try:
            if "login" in self.driver.current_url.lower():
                # Selector: button.btn-login.btn-other
                wait = WebDriverWait(self.driver, 5)
                btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-login.btn-other")))
                if btn:
                    if self.on_log: self.on_log("🤖 Tự động click đăng nhập Azure AD...")
                    btn.click()
                    time.sleep(2)
        except: pass

        while self.is_running:
            try:
                token = self.get_token(self.driver)
                if token:
                     if self.on_log: self.on_log("[SUCCESS] ĐÃ TÌM THẤY TOKEN!")
                     return "Bearer " + token
            except: pass
            time.sleep(2)
        return None

    def call_api(self, ticket_id, token, session):
        ticket_id = str(ticket_id).split('.')[0].strip()
        if not ticket_id or ticket_id.lower() == 'nan': return ""
        
        headers = {
            'Authorization': token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        try:
            # 1. API List
            url_list = f"https://ssc.fptshop.com.vn/api/v1/ticket-service/tasks/{ticket_id}"
            resp = session.get(url_list, headers=headers, timeout=10, verify=False)
            
            if resp.status_code == 401: return "EXPIRED"
            if resp.status_code != 200: return f"Lỗi {resp.status_code}"

            tasks = resp.json()
            target_task = None
            for t in tasks:
                 # Logic tìm task "kỹ thuật xử lý" như cũ
                if t.get('title') and "kỹ thuật xử lý" in t['title'].lower():
                    target_task = t
                    break
            
            if not target_task: return "Không tìm thấy bước xử lý (IT Support/Kỹ thuật)"

            # 2. API Detail
            task_id = target_task.get('taskId') if target_task else None
            if not task_id: return "Không lấy được Task ID"
            
            url_detail = f"https://ssc.fptshop.com.vn/api/v1/ticket-service/tasks/{ticket_id}/{task_id}"
            resp_detail = session.get(url_detail, headers=headers, timeout=10, verify=False)
            
            if resp_detail.status_code == 401: return "EXPIRED"
            
            detail_data = resp_detail.json()
            ket_qua = []
            
            # Debug/Log Logic: Check structure
            # Sometimes data is inside 'data' key, sometimes direct?
            # Based on code: detail_data.get('data', {})
            
            data_obj = detail_data.get('data', {})
            if not data_obj and isinstance(detail_data, dict):
                 # Fallback: maybe detail_data IS the data?
                 data_obj = detail_data

            if data_obj and isinstance(data_obj, dict):
                for key, val in data_obj.items():
                    # Filter out system keys if needed, or just take everything
                    if isinstance(val, str) and val.strip():
                        # Optional: Skip keys like 'taskId', 'processId' if they are irrelevant
                        if key in ['taskId', 'processId', 'createdTime']: continue
                        ket_qua.append(str(val).strip()) # type: ignore
            
            return " | ".join(ket_qua) if ket_qua else "ticket chưa phản hồi"

        except Exception as e:
            return f"Err: {e!s}"

    TOKEN_FILE = str(APP_TOKEN_FILE)

    def save_token(self, token):
        try:
            with open(self.TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(token.strip())
        except: pass
    
    def load_token(self):
        try:
            if os.path.exists(self.TOKEN_FILE):
                with open(self.TOKEN_FILE, "r", encoding="utf-8") as f:
                    token = f.read().strip()
                if token: return token
        except: pass
        return None

    def open_browser(self, headless=False):
        if self.driver:
            try:
                # Check if we need to switch from headless to visible
                if not headless and self.is_driver_headless:
                    if self.on_log: self.on_log("🔄 Đang chuyển từ chạy ngầm sang hiển thị...")
                    try: self.driver.quit()
                    except: pass
                    self.driver = None
                    self.is_shared_driver = False
                else:
                    _ = self.driver.current_url
                    if self.on_log: self.on_log("🔄 Đang dùng lại Chrome hiện có...")
                    return
            except:
                self.driver = None
                self.is_shared_driver = False

        if headless:
            if self.on_log: self.on_log("🌐 Đang thử kết nối ngầm (Headless)...")
        else:
            if self.on_log: self.on_log("🌐 Đang mở Chrome...")

        try:
            ensure_runtime_dirs()
            profile_path = str(CHROME_PROFILE_DIR)
            
            # Initial cleanup attempt to be safe, especially if starting fresh
            browser_manager.cleanup_chrome_sessions(profile_path)
            
            def create_driver():
                return browser_manager.create_chrome_driver(
                    profile_path=profile_path,
                    headless=headless,
                    use_manager=False,
                    detach=True,
                    start_maximized=not headless,
                    incognito=False,
                )

            try:
                self.driver = create_driver()
            except Exception as e:
                # If failed due to lock, try intensive cleanup and retry once
                msg = str(e).lower()
                if "session not created" in msg or "chrome instance exited" in msg:
                    if self.on_log: self.on_log("🧹 Phát hiện Chrome chạy ngầm, đang dọn dẹp để khởi động lại...")
                    browser_manager.cleanup_chrome_sessions(profile_path)
                    time.sleep(2)
                    self.driver = create_driver()
                else:
                    raise e

            self.is_driver_headless = headless
            self.driver.get(URL_LOGIN)
        except Exception as e:
            msg = str(e)
            if "session not created" in msg.lower() or "chrome instance exited" in msg.lower():
                if self.on_log: self.on_log("[FAIL] LỖI: Vẫn không thể mở Chrome. Vui lòng kiểm tra Task Manager và tắt hết các tiến trình Chrome/Chromedriver bằng tay.")
            else:
                 if self.on_log: self.on_log(f"[WARN] Lỗi khởi tạo Chrome: {e}")

    def run(self):
        try:
            token = self.load_token()
            use_cached_token = False

            # Check if we assume cached token is good (optimistic)
            # OR we can validate it immediately if we have a ticket ID.
            
            # 1. Determine Data Source first to get a sample Ticket ID for validation
            df = None
            if self.dataframe is not None:
                df = self.dataframe
                if self.on_log: self.on_log("📊 Sử dụng dữ liệu từ Google Sheet...")
            elif self.file_path:
                if self.file_path.lower().endswith('.csv'):
                    try: df = pd.read_csv(self.file_path, encoding='utf-8-sig')
                    except: df = pd.read_csv(self.file_path, encoding='cp1252')
                else:
                    df = pd.read_excel(self.file_path)
            else:
                if self.on_log: self.on_log("[FAIL] Không có dữ liệu để xử lý")
                return

            # Determine Columns (always use index 3 for Ticket due to normalization)
            # Find the Ticket column index by name (fallback to 3)
            current_ticket_col = 3
            for i, col in enumerate(df.columns):
                if str(col).lower().strip() in ['ticket_id', 'ticket id', 'id', 'ticket']:
                    current_ticket_col = i
                    break

            if self.is_no_data:
                result_col_letter = "G" # G
            elif self.is_hdd:
                result_col_letter = "F" # F
            elif self.is_dvr:
                result_col_letter = "G" # G
            else:
                result_col_letter = "J" # J (Nội dung ticket di chuyển sang cột J)

            if len(df.columns) <= current_ticket_col:
                if self.on_log: self.on_log(f"[FAIL] Dữ liệu lỗi: Thiếu cột Ticket ID tại index {current_ticket_col}")
                return
            
            # Try validating cached token with first ticket
            if token and not self.driver: # Only verify if no driver open
                first_ticket = str(df.iloc[0, current_ticket_col])
                if self.on_log: self.on_log("♻️ Đang kiểm tra Token cũ...")
                with requests.Session() as s:
                    res = self.call_api(first_ticket, token, s)
                    if res != "EXPIRED":
                        if self.on_log: self.on_log("[SUCCESS] Token cũ vẫn tốt! Chạy ngầm không cần Chrome.")
                        use_cached_token = True
                    else:
                        if self.on_log: self.on_log("[WARN] Token cũ hết hạn.")
                        token = None

            # 2. If no valid cached token, Open Browser
            if not use_cached_token:
                # STRATEGY: Try Headless First -> If fail -> Visible
                if not self.driver:
                    # Try Headless First
                    self.open_browser(headless=True)
                    
                    # Wait shortly for auto-login
                    if self.on_log: self.on_log("[WAIT] Đang đợi đăng nhập tự động...")
                    
                    # Custom wait loop with timeout for Headless
                    found_token = False
                    for _ in range(5): # Wait 10s (5 * 2s)
                        if not self.is_running: break
                        t = self.get_token(self.driver)
                        if t:
                            token = "Bearer " + t
                            found_token = True
                            if self.on_log: self.on_log("[SUCCESS] Tự động đăng nhập thành công!")
                            self.save_token(token)
                            break
                        time.sleep(2)
                    
                    if not found_token:
                        if self.on_log: self.on_log("[WARN] Không thể tự đăng nhập. Đang chuyển sang chế độ thủ công...")
                        try: self.driver.quit()
                        except: pass
                        self.driver = None
                        
                        # Open Visible Browser
                        self.open_browser(headless=False)
                        token = self.wait_for_login() # Wait indefinitely for user
                        if token: self.save_token(token)
                        else: return

                else:
                    if self.on_log: self.on_log("🔗 Đang dùng lại Chrome hiện có...")
                    # Wait for login if browser is open (and no token)
                    if not token: 
                        token = self.wait_for_login()
                        if token: self.save_token(token)
                        else: return

            elif use_cached_token:
                if self.on_log: self.on_log("🚀 Chế độ chạy ngầm (Headless) kích hoạt.")

            # 4. Process
            total = len(df)
            results = []
            
            if not isinstance(df, pd.DataFrame): return

            with requests.Session() as session:
                assert isinstance(df, pd.DataFrame)
                for index, row in df.iterrows(): # type: ignore
                    if not self.is_running: break
                    
                    ticket_id = row.iloc[current_ticket_col]
                    if self.on_log: self.on_log(f"Checking {index+1}/{total}: {ticket_id}")
                    if self.on_progress: self.on_progress(index+1, total)
                    
                    res = self.call_api(ticket_id, token, session)
                    
                    if res == "EXPIRED":
                        if self.on_log: self.on_log("♻️ Token hết hạn! Đang mở cửa sổ đăng nhập...")
                        try:
                            self.open_browser(headless=False) # Ensure browser is VISIBLE
                            self.driver.refresh()
                            time.sleep(5)
                            token = self.wait_for_login()
                            if token: 
                                self.save_token(token)
                                res = self.call_api(ticket_id, token, session)
                            else: 
                                res = "Lỗi Login"
                        except Exception as e: 
                            res = f"Lỗi Refresh: {e}"
                            if self.on_log: self.on_log(str(e))
                    
                    results.append(res)
                    time.sleep(0.05)
            
            # 5. Export Results
            assert isinstance(df, pd.DataFrame)
            if len(results) < len(df):
                results.extend([""] * (len(df) - len(results)))
            df['Ket_Qua_Auto'] = results # type: ignore
            
            # Check mode: File or GSheet
            if self.file_path:
                # File mode - export to Excel
                folder = os.path.dirname(self.file_path)
                fname = f"{os.path.basename(self.file_path).split('.')[0]}_CHECK_KQ.xlsx"
                out_path = os.path.join(folder, fname)
                if isinstance(df, pd.DataFrame):
                    df.to_excel(out_path, index=False)
                if self.on_finished: self.on_finished({"success": True, "output_file": {"available": True, "filename": os.path.basename(out_path)}, "message": f"Đã lưu kết quả tại: {os.path.basename(out_path)}"})
            else:
                # GSheet mode - write results back to dynamic column
                if self.on_log: self.on_log(f"☁ Đang ghi kết quả lên Google Sheet (Cột {result_col_letter})...")
                try:
                    from app.services import gsheet_sync  # type: ignore
                    
                    # Determine target sheet name
                    if self.is_no_data:
                        target_sheet = gsheet_sync.SHEET_NO_DATA
                        ticket_col_idx = 6 # F
                    elif self.is_hdd:
                        target_sheet = gsheet_sync.SHEET_HDD
                        ticket_col_idx = 5 # E
                    elif self.is_dvr:
                        target_sheet = gsheet_sync.SHEET_DVR
                        ticket_col_idx = 6 # F
                    else:
                        target_sheet = gsheet_sync.SHEET_CAM_MKN
                        ticket_col_idx = 7 # G
                        
                    # Create map of ticket_id to result
                    ticket_results_map = {}
                    for idx, row in df.iterrows():
                        t_id = str(row.iloc[current_ticket_col]).split('.')[0].strip()
                        if t_id and t_id.lower() != 'nan':
                            ticket_results_map[t_id] = results[idx]

                    ok, msg = gsheet_sync.update_ticket_status_by_id(
                        ticket_results_map=ticket_results_map, 
                        sheet_name=target_sheet, 
                        col_letter=result_col_letter,
                        ticket_col_index=ticket_col_idx,
                        logger=self.on_log
                    )
                    if ok:
                        if self.on_finished: self.on_finished({"success": True, "output_file": {"available": False, "filename": None}, "message": f"[GSheet] Đã cập nhật cột {result_col_letter} thành công!"})
                    else:
                        if self.on_finished: self.on_finished({"success": False, "output_file": {"available": False, "filename": None}, "message": f"[GSheet] Lỗi: {msg}"})
                except Exception as e:
                    if self.on_finished: self.on_finished({"success": False, "output_file": {"available": False, "filename": None}, "message": f"[GSheet] Lỗi ghi: {e}"})


        except Exception as e:
             import traceback
             if self.on_log: self.on_log(f"[FAIL] Lỗi Run: {e}\n{traceback.format_exc()}")
        finally:
            # Only quit if WE opened the driver (not shared) AND we actually opened it
             if self.driver and not self.is_shared_driver:
                 # Optional: Keep open if user wants? For now close to be clean unless reused
                 # User said "chỉ mở khi hết hạn", implying we usually don't need it.
                 # If we opened it just for token, maybe close it?
                 # Let's keep it open if we want to save startup time next run?
                 # But if we close, next time we use token.
                 # Let's quit to save resources if we used it.
                 try: self.driver.quit()
                 except: pass






