import re
import re
import sys
import os
import time
import datetime
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from app.services import browser_manager
from app.services import ticket_service
from app.paths import CHROME_PROFILE_DIR, ensure_runtime_dirs

class TicketScanner:
# Signal to send driver back to widget
    
    def __init__(self, driver, data_list, sys_mode, func_name, is_gsheet_mode=False, is_dvr=False, is_no_data=False, is_hdd=False):
        self.on_log = None
        self.on_driver = None
        self.on_finished = None
        self.driver = driver
        self.data_list = data_list
        self.sys_mode = sys_mode
        self.func_name = func_name
        self.is_gsheet_mode = is_gsheet_mode
        self.is_dvr = is_dvr
        self.is_no_data = is_no_data
        self.is_hdd = is_hdd
        self.is_running = True

    def stop(self):
        self.is_running = False

    def get_value_flexible(self, row, keys):
        """
        Helper to find value from row using multiple possible keys (case-insensitive).
        """
        keys_lower = [k.lower() for k in keys]
        for k in row.keys():
            if k.lower() in keys_lower:
                val = row[k]
                if pd.notnull(val) and str(val).strip() != '':
                     return val
        return None

    def run(self):
        if self.on_log: self.on_log(f"🚀 Bắt đầu ({self.sys_mode} - {self.func_name})...")
        
        if not self.is_running: return

        # --- PRE-PROCESSING: Group rows by ma_shop ---
        grouped_data = [] # List of dicts
        shop_to_idx = {} # ma_shop -> index in grouped_data
        
        for original_idx, row in enumerate(self.data_list):
            # Extract ma_shop
            ma = str(self.get_value_flexible(row, ['ma_shop', 'Shop Code', 'Mã shop', 'Mã kho']) or '').strip()
            ma = ma.removesuffix('.0')
            if not ma: ma = "Unknown"
            
            # Extract cam info from all possible columns
            raw_cam = self.get_value_flexible(row, [
                'Danh sách cam offline', 'Danh sách Cam lỗi', 'CH/Chi tiết', 
                'Số Cam', 'CH', 'Mã Cam', 'camera_mkn', 'Camera', 'Chi tiết',
                'Cam mới offline', 'Cam cũ vẫn lỗi', 'Cam đã online'
            ])
            cams = [c.strip() for c in str(raw_cam or '').split(',') if c.strip()]
            
            if ma not in shop_to_idx:
                shop_to_idx[ma] = len(grouped_data)
                new_item = row.copy()
                new_item['_ma_shop_norm'] = ma
                new_item['_collected_cams'] = set(cams)
                new_item['_original_indices'] = [original_idx]
                grouped_data.append(new_item)
            else:
                idx = shop_to_idx[ma]
                grouped_data[idx]['_collected_cams'].update(cams)
                grouped_data[idx]['_original_indices'].append(original_idx)

        # 0. Initialize Browser if needed
        if not self.driver:
            if self.on_log: self.on_log("🌐 Đang khởi tạo trình duyệt...")
            try:
                ensure_runtime_dirs()
                profile_path = str(CHROME_PROFILE_DIR)
                
                if not self.is_running: return
                self.driver = browser_manager.create_chrome_driver(
                    profile_path=profile_path,
                    headless=False,
                    use_manager=False,
                    detach=False,
                    start_maximized=True,
                    incognito=False,
                )
                if not self.is_running:
                    try: self.driver.quit()
                    except: pass
                    self.driver = None
                    return
                
                if self.on_driver: self.on_driver(self.driver) # Update Widget's driver
                
                self.driver.get(ticket_service.CREATE_URL)
                if not self.is_running: return
                time.sleep(2)
                
                # Auto-click Azure AD
                if "login" in self.driver.current_url.lower():
                    try:
                        btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-login.btn-other"))
                        )
                        if not self.is_running: return
                        if self.on_log: self.on_log("🤖 Tự động click Azure AD...")
                        btn.click()
                        time.sleep(2)
                    except: pass
            except Exception as e:
                msg = str(e)
                if "chrome instance exited" in msg.lower():
                    if self.on_log: self.on_log("[FAIL] LỖI: Cửa sổ Chrome bị đóng bất ngờ!")
                elif "session not created" in msg.lower():
                    if self.on_log: self.on_log(f"[FAIL] Lỗi phiên trình duyệt: {msg}")
                else:
                    if self.on_log: self.on_log(f"[FAIL] Lỗi trình duyệt: {e}")
                if self.on_finished: self.on_finished({"success": False, "output_file": {"available": False, "filename": None}, "message": f"Không thể khởi động trình duyệt: {msg}"})
                return

        for i, data in enumerate(grouped_data):
            if not self.is_running: break
            
            ma_shop = data['_ma_shop_norm']

            # Check if any of the grouped rows already has a ticket_id
            ticket_id = None
            ticket_date = None
            for o_idx in data['_original_indices']:
                tid = self.get_value_flexible(self.data_list[o_idx], ['ticket_id', 'Ticket ID', 'ID', 'Ticket_ID', 'Ticket'])
                if tid and str(tid).lower() not in ['nan', '', 'none']:
                    ticket_id = tid
                    ticket_date = self.get_value_flexible(self.data_list[o_idx], ['Ngày tạo ticket', 'Ngày tạo', 'Created Date'])
                    break
            
            if ticket_id and str(ticket_id).lower() not in ['nan', '', 'none']:
                msg = f"⏭ Shop {ma_shop} đã có Ticket ({ticket_id}) -> Bỏ qua"
                if self.on_log: self.on_log(msg)
                
                # Sync ID back to all original rows in memory AND in Google Sheets
                for o_idx in data['_original_indices']:
                    orig_tid = self.get_value_flexible(self.data_list[o_idx], ['ticket_id', 'Ticket ID', 'ID', 'Ticket_ID', 'Ticket'])
                    if not orig_tid or str(orig_tid).lower() in ['nan', '', 'none']:
                        # Row is missing the ticket ID, update it
                        self.data_list[o_idx]['ticket_id'] = str(ticket_id)
                        
                        if getattr(self, 'is_gsheet_mode', False):
                            try:
                                from app.services import gsheet_sync
                                if self.is_no_data:
                                    target_col = 6
                                    sheet_n = gsheet_sync.SHEET_NO_DATA
                                elif self.is_hdd:
                                    target_col = 5
                                    sheet_n = gsheet_sync.SHEET_HDD
                                else:
                                    target_col = 6 if self.is_dvr else 7
                                    sheet_n = gsheet_sync.SHEET_DVR if self.is_dvr else gsheet_sync.SHEET_CAM_MKN
                                
                                # Use ticket_date if available, else fallback
                                row_date = self.get_value_flexible(self.data_list[o_idx], ['Ngày tạo ticket', 'Ngày tạo', 'Created Date', 'Ngày'])
                                created_d = str(row_date) if row_date else (str(ticket_date) if ticket_date else None)
                                
                                gsheet_sync.update_ticket_id_single(
                                    o_idx, str(ticket_id), sheet_name=sheet_n, col_index=target_col, created_date=created_d, preserve_existing_date=True
                                )
                            except Exception:
                                pass
                continue

            if not self.is_running: break
            try:
                # 2. Location / Region
                raw_loc = self.get_value_flexible(data, ['Vùng', 'Region', 'Khu vực', 'location', 'Miền'])
                
                raw_loc = str(raw_loc) if raw_loc else ''
                
                if not raw_loc or raw_loc.lower() == 'nan':
                    if self.on_log: self.on_log(f"[WARN] Shop {ma_shop}: Thiếu Location/Vùng")
                    continue

                real_loc = self.convert_location(raw_loc, self.sys_mode)
                
                # 3. Camera Name: Merge all collected cams
                if self.is_dvr or self.is_hdd:
                    real_cam = "Đầu gửi" if self.is_dvr else "Đầu ghi" 
                    # Note: User request for HDD says "Đầu ghi không có playback"
                    # But for cam name usually "Đầu ghi" is fine.
                    if self.is_hdd: real_cam = "Đầu ghi"
                else:
                    # Normalize and join
                    cams_list = sorted(data['_collected_cams'])
                    norm_cams = []
                    for c in cams_list:
                        # Simple check to avoid double-normalizing if already CHxx
                        if re.match(r"^CH\d+$", c, re.IGNORECASE):
                            norm_cams.append(c.upper())
                        elif ',' not in c and ' ' not in c.strip() and len(c) < 10:
                            norm_cams.append(self.normalize_camera(c))
                        else:
                            norm_cams.append(c)
                    
                    real_cam = ", ".join(norm_cams)
                
                if not real_cam: real_cam = 'Camera'

                if self.on_log: self.on_log(f"🔄 [{i+1}/{len(grouped_data)}] Shop {ma_shop} | {real_loc} | {real_cam}...")

                try:
                    if "CreateTicket" not in self.driver.current_url:
                        self.driver.get(ticket_service.CREATE_URL)
                        time.sleep(1.5)
                        if "login" in self.driver.current_url.lower():
                            try:
                                btn = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-login.btn-other"))
                                )
                                btn.click()
                                time.sleep(2)
                            except: pass
                except Exception as e:
                    if self.on_log: self.on_log(f"[FAIL] Lỗi Browser: {e}")
                    self.is_running = False 
                    break

                temp_data = data.copy()
                temp_data['ma_shop'] = ma_shop
                temp_data['ten_shop'] = self.get_value_flexible(data, ['ten_shop', 'Tên shop', 'Shop Name']) or ''
                
                t_id_result = self.create_single_ticket(temp_data, real_loc, real_cam, self.func_name, self.is_dvr, self.is_no_data, self.is_hdd)
                
                if t_id_result:
                    # Update all original rows
                    for o_idx in data['_original_indices']:
                        self.data_list[o_idx]['ticket_id'] = t_id_result
                        
                        # Real-time Update GSheet for EACH row
                        if self.is_gsheet_mode:
                            try:
                                from app.services import gsheet_sync
                                if self.is_no_data:
                                    target_col = 6 # F (1-based for gspread)
                                    sheet_n = gsheet_sync.SHEET_NO_DATA
                                elif self.is_hdd:
                                    target_col = 5 # E
                                    sheet_n = gsheet_sync.SHEET_HDD
                                else:
                                    target_col = 6 if self.is_dvr else 7 # Col G (7) for Cam mkn, Col F (6) for Lỗi đầu ghi
                                    sheet_n = gsheet_sync.SHEET_DVR if self.is_dvr else gsheet_sync.SHEET_CAM_MKN
                                from datetime import datetime
                                row_date = self.get_value_flexible(self.data_list[o_idx], ['Ngày tạo ticket', 'Ngày tạo', 'Created Date', 'Ngày'])
                                created_d = str(row_date) if row_date else datetime.now().strftime("%d/%m/%Y")
                                ok_rt, msg_rt = gsheet_sync.update_ticket_id_single(
                                    o_idx, t_id_result, sheet_name=sheet_n, col_index=target_col, created_date=created_d, preserve_existing_date=True
                                )
                            except Exception: pass
                    
                    if self.on_log: self.on_log(f"[SUCCESS] OK: Ticket ID {t_id_result}")
                else:
                    if self.on_log: self.on_log(f"[FAIL] Failed: Shop {ma_shop}")

            except Exception as e:
                if self.on_log: self.on_log(f"[FAIL] Error shop {ma_shop}: {e}")
            
            time.sleep(1)
        
        if self.on_finished: self.on_finished({"success": True, "output_file": {"available": False, "filename": None}, "message": "Hoàn tất tạo Ticket."})

    def convert_location(self, raw_loc, sys_mode):
        return ticket_service.convert_location(raw_loc, sys_mode)

    def normalize_camera(self, raw_cam):
        return ticket_service.normalize_camera(raw_cam)

    def create_single_ticket(self, data, location, camera_text, func_name, is_dvr=False, is_no_data=False, is_hdd=False):
        if not self.is_running: return None
        wait = WebDriverWait(self.driver, 30)

        # Subject: ShopCode | ShopName : Camera...
        ma = data.get('ma_shop', '')
        ten = data.get('ten_shop', '')
        subject = ticket_service.build_subject(ma, ten, camera_text, is_dvr, is_no_data, is_hdd)
        
        try:
            # Subject
            try:
                if not self.is_running: return None
                subj = wait.until(EC.visibility_of_element_located((By.ID, ticket_service.ID_SUBJECT)))
            except:
                if not self.is_running: return None
                subj = wait.until(EC.visibility_of_element_located((By.NAME, ticket_service.NAME_SUBJECT)))
            
            if not self.is_running: return None
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].focus();", subj)
            subj.clear()
            self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", subj, subject)
            time.sleep(0.5)

            # Location (Select2)
            if not self.force_open_select2_by_id(ticket_service.ID_LOCATION_CONTAINER, location):
                if not self.force_open_select2_by_id("sms-ticket-location", location):
                    if self.on_log: self.on_log(f"[WARN] Không chọn được Vị trí: {location}")
                return None
            
            # Function Group (Select2)
            if not self.force_open_select2_by_xpath_relative("Nhóm chức năng", func_name):
                if self.on_log: self.on_log(f"[WARN] Không chọn được Nhóm chức năng: {func_name}")
                return None

            # Description
            content = ticket_service.build_description(camera_text, is_dvr, is_no_data, is_hdd)
            try:
                # Robustly find the first visible textarea
                textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
                try:
                    desc = wait.until(EC.presence_of_element_located((By.XPATH, ticket_service.XPATH_TEXTAREA)))
                except:
                    desc = next((ta for ta in textareas if ta.is_displayed()), None)
                if not desc:
                    desc = wait.until(EC.visibility_of_element_located((By.XPATH, ticket_service.XPATH_TEXTAREA)))
                
                # Use JS to scroll and clear just in case
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", desc)
                time.sleep(0.5)
                desc.clear()
                self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", desc, content)
                time.sleep(0.5)
                # Trigger validation explicitly
                desc.send_keys(" ")
                desc.send_keys(Keys.BACKSPACE)
                # Or click out
                try: self.driver.find_element(By.TAG_NAME, 'body').click()
                except: pass
            except: pass

            if not self.is_running: return None
            # Submit
            try:
                if not self.is_running: return None
                # Try ID first
                try: btn = self.driver.find_element(By.ID, ticket_service.ID_SUBMIT)
                except: btn = None
                
                # Try Text "Gửi" if ID failed
                if not btn:
                    if not self.is_running: return None
                    try: btn = self.driver.find_element(By.XPATH, ticket_service.XPATH_SUBMIT_GZ)
                    except: btn = None
                
                # Last resort: Any button with type submit?
                if not btn:
                    try: btn = self.driver.find_element(By.XPATH, ticket_service.XPATH_SUBMIT_GENERIC)
                    except: pass
                
                if btn:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.5)
                    try: btn.click()
                    except: self.driver.execute_script("arguments[0].click();", btn)
                else:
                    return None
            except: return None
            
            # Get Ticket ID
            try:
                if not self.is_running: return None
                view_btn = wait.until(EC.presence_of_element_located((By.ID, ticket_service.ID_VIEW_TICKET)))
                href = view_btn.get_attribute("href")
                match = re.search(r'id=(\d+)', href)
                t_id = match.group(1) if match else "Done"
                
                # Reset for next
                self.driver.get(ticket_service.CREATE_URL)
                wait.until(EC.visibility_of_element_located((By.ID, "sms-ticket-title-real")))
                return t_id
            except:
                self.driver.get(ticket_service.CREATE_URL)
                return None
        except:
            return None

    # ... (force_open_select2 helpers UNCHANGED)
    def force_open_select2_by_id(self, container_or_input_id, text_value):
        try:
            wait = WebDriverWait(self.driver, 15)
            real_id = container_or_input_id.removeprefix("s2id_")
            container_id = f"s2id_{real_id}"

            opened = self.driver.execute_script(f"""
                try {{
                    if (window.jQuery) {{
                        var $el = jQuery('#{real_id}');
                        if ($el.length) {{
                            $el.select2('open');
                            return true;
                        }}
                    }}
                    var choice = document.querySelector('#{container_id} .select2-choice') || document.querySelector('#{real_id}');
                    if (choice) {{
                        choice.scrollIntoView({{block: 'center'}});
                        choice.click();
                        return true;
                    }}
                }} catch(e) {{}}
                return false;
            """)

            if not opened:
                try:
                    arrow_xpath = f"//div[@id='{container_id}']//a[contains(@class, 'select2-choice')] | //div[@id='{container_id}']//b"
                    arrow = wait.until(EC.presence_of_element_located((By.XPATH, arrow_xpath)))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", arrow)
                except Exception:
                    pass

            inp = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@id='select2-drop']//input[contains(@class, 'select2-input')]")))
            inp.clear()
            inp.send_keys(text_value)
            time.sleep(1)
            inp.send_keys(Keys.ENTER)
            time.sleep(0.5)
            return True
        except Exception:
            return False

    def force_open_select2_by_xpath_relative(self, label_text, text_value):
        try:
            wait = WebDriverWait(self.driver, 15)
            opened = self.driver.execute_script(f"""
                try {{
                    var inp = document.querySelector("input[name='{label_text}']");
                    if (inp && window.jQuery) {{
                        jQuery(inp).select2('open');
                        return true;
                    }}
                    if (inp && inp.nextElementSibling) {{
                        var choice = inp.nextElementSibling.querySelector('.select2-choice');
                        if (choice) {{
                            choice.scrollIntoView({{block: 'center'}});
                            choice.click();
                            return true;
                        }}
                    }}
                }} catch(e) {{}}
                return false;
            """)

            if not opened:
                xpath = f"//div[contains(@class, 'name')]//div[contains(text(), '{label_text}')]/following::div[contains(@class, 'select2-container')][1]"
                container = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                cid = container.get_attribute("id")
                if cid and self.force_open_select2_by_id(cid, text_value):
                    return True
                choice = container.find_element(By.CSS_SELECTOR, ".select2-choice")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", choice)

            inp = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@id='select2-drop']//input[contains(@class, 'select2-input')]")))
            inp.clear()
            inp.send_keys(text_value)
            time.sleep(1)
            inp.send_keys(Keys.ENTER)
            time.sleep(0.5)
            return True
        except Exception:
            return False
