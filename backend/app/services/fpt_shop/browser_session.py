import os
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
from app.services.browser.browser_manager import BaseBrowserSession

logger = logging.getLogger(__name__)

class FPTBrowserSession(BaseBrowserSession):
    _instance = None
    _singleton_lock = threading.Lock()

    def __init__(self):
        super().__init__(
            profile_name="fpt-shop-profile",
            start_url="https://calllog.fptshop.com.vn/Report/DebtConfirm"
        )
        self.temp_creds = None
        
    @classmethod
    def get_instance(cls):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = FPTBrowserSession()
        return cls._instance

    def _force_show_window(self):
        if os.name != 'nt':
            return
        try:
            if not self.driver:
                return
            self.driver.maximize_window()
            import ctypes
            title = self.driver.title or ""
            hwnd = ctypes.windll.user32.FindWindowW(None, title + " - Google Chrome")
            if not hwnd:
                hwnd = ctypes.windll.user32.FindWindowW(None, title)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 5) # SW_SHOW
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    def _force_minimize_window(self):
        if os.name != 'nt':
            return
        try:
            if not self.driver:
                return
            try:
                self.driver.minimize_window()
            except Exception:
                pass
            import ctypes
            title = self.driver.title or ""
            candidates = [
                title + " - Google Chrome",
                title,
                "Báo cáo Chi tiết thiết bị - Hệ thống CallLog - Google Chrome",
                "Báo cáo Chi tiết thiết bị - Google Chrome",
                "CallLog - Google Chrome"
            ]
            hwnd = None
            for c in candidates:
                if c.strip():
                    hwnd = ctypes.windll.user32.FindWindowW(None, c)
                    if hwnd:
                        break
            if not hwnd:
                hwnd = ctypes.windll.user32.FindWindowW("Chrome_WidgetWin_1", None)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 6) # SW_MINIMIZE
        except Exception:
            pass

    def _is_on_target_page(self) -> bool:
        if not self.driver:
            return False
        url = self.driver.current_url.lower()
        if "calllog.fptshop.com.vn/report/debtconfirm" in url:
            return True
        if "identity.fptshop.com.vn" in url or "accounts.google.com" in url or "microsoftonline.com" in url:
            # We are in the auth flow, do not redirect
            return True
        return False

    def start(self, probe_only=False, headless=False):
        self._closing_thread_started = False
        return super().start(probe_only=probe_only, headless=headless)

    def get_status(self):
        with self._lock:
            if self.driver is None:
                if self.status == "AUTHENTICATED":
                    return self.status
                if self.status != "ERROR":
                    self.status = "STOPPED"
                return self.status
                
            try:
                url = self.driver.current_url.lower()
                
                if "calllog.fptshop.com.vn/report/debtconfirm" in url:
                    self.status = "AUTHENTICATED"
                    self._force_minimize_window()
                    
                    # Close the visible browser window after completing authentication so it doesn't linger on screen
                    def switch_headless():
                        try:
                            import time
                            time.sleep(1.0)
                            driver_to_quit = None
                            with self._lock:
                                if self.driver and not getattr(self, 'is_headless', False):
                                    driver_to_quit = self.driver
                                    self.clear_driver()
                            if driver_to_quit:
                                try:
                                    driver_to_quit.quit()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    
                    if not getattr(self, '_closing_thread_started', False) and not getattr(self, 'is_headless', False):
                        self._closing_thread_started = True
                        threading.Thread(target=switch_headless, daemon=True).start()
                    
                elif "identity.fptshop.com.vn" in url:
                    try:
                        # ALWAYS Inject credentials if provided on this domain!
                        js = """
                        let pwd = document.querySelector('input[name="LoginInput.Password"]') || document.querySelector('input[formcontrolname="password"]') || document.querySelector('input[type="password"]');
                        let acc = document.querySelector('input[name="LoginInput.UserNameOrEmailAddress"]') || document.querySelector('input[formcontrolname="employee_code"]') || document.querySelector('input[name="UserName"]') || document.querySelector('input[type="text"]');
                        
                        let providedUser = arguments[0];
                        let providedPass = arguments[1];
                        
                        if (providedUser && providedPass && pwd && acc && (!pwd.value || !acc.value)) {
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            
                            nativeInputValueSetter.call(acc, providedUser);
                            acc.dispatchEvent(new Event('input', { bubbles: true }));
                            
                            nativeInputValueSetter.call(pwd, providedPass);
                            pwd.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                        """
                        user = self.temp_creds.get("username") if getattr(self, "temp_creds", None) else ""
                        pwd = self.temp_creds.get("password") if getattr(self, "temp_creds", None) else ""
                        self.driver.execute_script(js, user, pwd)
                    except Exception as e:
                        pass

                    # Then check for OTP required
                    page_source = self.driver.page_source.lower()
                    if "otp" in page_source or "mã xác nhận" in page_source or "authenticator" in page_source or "verification" in page_source:
                        self.status = "OTP_REQUIRED"
                        self._force_show_window()
                    else:
                        self.status = "LOGIN_PAGE"

                elif "accounts.google.com" in url or "login.microsoftonline.com" in url:
                    self.status = "OTP_REQUIRED"
                    self._force_show_window()
                else:
                    self.status = "UNKNOWN"
                    self._force_show_window()
                        
            except Exception as e:
                if self.status != "AUTHENTICATED":
                    logger.error(f"FPT browser session lost: {e}")
                    self.status = "STOPPED"
                self.clear_driver()
                
            return self.status
