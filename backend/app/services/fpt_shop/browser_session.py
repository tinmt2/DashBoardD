import os
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
        self.temp_creds = self._load_creds()
        
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
        if "login" in url or "identity" in url:
            return False
        if "calllog.fptshop.com.vn/report/debtconfirm" in url:
            return True
        return False

    def start(self, probe_only=False, headless=False):
        self._closing_thread_started = False
        self._auto_otp_attempted = False
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
                
                # Check if we are on a login / identity page first!
                is_login = "users/login" in url or "identity.fptshop.com.vn" in url or "identity.frt.vn" in url or ("login" in url and "calllog.fptshop" in url) or "/account/login" in url
                
                if is_login:
                    try:
                        # ALWAYS Inject credentials and auto-submit if provided
                        js = """
                        let pwd = document.querySelector('input[name="LoginInput.Password"]') || document.querySelector('input[formcontrolname="password"]') || document.querySelector('input[type="password"]');
                        let acc = document.querySelector('input[name="LoginInput.UserNameOrEmailAddress"]') || document.querySelector('input[formcontrolname="employee_code"]') || document.querySelector('input[name="UserName"]') || document.querySelector('input[type="text"]');
                        let otpInput = document.querySelector('input[name="LoginInput.Otp"]') || document.querySelector('input.input-otp') || document.querySelector('input[formcontrolname="otp"]');
                        
                        let providedUser = arguments[0];
                        let providedPass = arguments[1];
                        let providedOtp = arguments[2];
                        
                        if (providedUser && providedPass && pwd && acc) {
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            
                            nativeInputValueSetter.call(acc, providedUser);
                            acc.dispatchEvent(new Event('input', { bubbles: true }));
                            acc.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            nativeInputValueSetter.call(pwd, providedPass);
                            pwd.dispatchEvent(new Event('input', { bubbles: true }));
                            pwd.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            if (providedOtp && otpInput) {
                                nativeInputValueSetter.call(otpInput, providedOtp);
                                otpInput.dispatchEvent(new Event('input', { bubbles: true }));
                                otpInput.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                            
                            let btn = document.querySelector('#kt_login_signin_submit') || document.querySelector('button[type="submit"]') || document.querySelector('.kt-login__btn-primary');
                            if (btn && !window._fpt_submitted) {
                                window._fpt_submitted = true;
                                setTimeout(() => btn.click(), 400);
                            }
                        }
                        """
                        user = self.temp_creds.get("username") if getattr(self, "temp_creds", None) else ""
                        pwd = self.temp_creds.get("password") if getattr(self, "temp_creds", None) else ""
                        otp = self.temp_creds.get("otp") if getattr(self, "temp_creds", None) else ""
                        if user and pwd:
                            self.driver.execute_script(js, user, pwd, otp)
                    except Exception as e:
                        pass

                    page_source = self.driver.page_source.lower()
                    has_otp_field = False
                    try:
                        has_otp_field = bool(self.driver.find_elements(By.NAME, "LoginInput.Otp") or self.driver.find_elements(By.CLASS_NAME, "input-otp"))
                    except: pass

                    if "tài khoản hoặc mật khẩu không chính xác" in page_source:
                        self.status = "LOGIN_FAILED"
                    elif "mã xác thực không hợp lệ" in page_source or "mã xác nhận không đúng" in page_source or "mã otp không đúng" in page_source or "otp không chính xác" in page_source:
                        self.status = "OTP_INVALID"
                        self._force_show_window()
                    elif has_otp_field or "vui lòng nhập mã otp" in page_source:
                        # Auto-fill OTP if Secret Key is configured
                        from app.core.totp import get_current_totp_code
                        auto_otp = get_current_totp_code()
                        if auto_otp and not getattr(self, "_auto_otp_attempted", False):
                            self._auto_otp_attempted = True
                            logger.info(f"[{self.profile_name}] Tự động lấy mã TOTP từ Authenticator Secret và submit...")
                            self.submit_otp(auto_otp)
                            return self.get_status()
                        self.status = "OTP_REQUIRED"
                        self._force_show_window()
                    else:
                        self.status = "LOGIN_PAGE"

                elif "calllog.fptshop.com.vn/report/debtconfirm" in url and "login" not in url and "identity" not in url:
                    cookies_dict = {}
                    try:
                        cookies_dict = {c['name']: c['value'] for c in self.driver.get_cookies()}
                    except: pass
                    
                    is_report_loaded = False
                    try:
                        is_report_loaded = bool(self.driver.find_elements(By.NAME, "timeStart") or self.driver.find_elements(By.ID, "timeStart") or "chi tiết thiết bị" in self.driver.page_source.lower() or "giám sát" in self.driver.page_source.lower())
                    except: pass
                    
                    has_auth_cookie = any(k in cookies_dict for k in ['.AspNet', '.AspNetCore', 'idsrv', 'calllog'])
                    
                    if is_report_loaded or has_auth_cookie:
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
                    else:
                        # Page is still in transit / redirecting
                        self.status = "STARTING"

                elif "accounts.google.com" in url or "login.microsoftonline.com" in url:
                    self.status = "OTP_REQUIRED"
                    self._force_show_window()
                else:
                    self.status = "UNKNOWN"
                    self._force_show_window()
                        
            except Exception as e:
                err_str = str(e).lower()
                if "invalid session id" in err_str or "not connected to devtools" in err_str:
                    logger.debug(f"FPT browser closed: {e}")
                elif self.status != "AUTHENTICATED":
                    logger.warning(f"FPT browser session lost: {e}")
                    self.status = "STOPPED"
                self.clear_driver()
                
            return self.status

    def submit_otp(self, otp: str, username: str = "", password: str = "") -> str:
        with self._lock:
            if not self.driver:
                return "STOPPED"
            try:
                if username and password:
                    self.temp_creds = {"username": username, "password": password}
                    self._save_creds(self.temp_creds)

                user = username or (self.temp_creds.get("username") if getattr(self, "temp_creds", None) else "")
                pwd = password or (self.temp_creds.get("password") if getattr(self, "temp_creds", None) else "")

                js = """
                let code = arguments[0];
                let user = arguments[1] || "";
                let pass = arguments[2] || "";

                let acc = document.querySelector('input[name="LoginInput.UserNameOrEmailAddress"]') || document.querySelector('input[formcontrolname="employee_code"]') || document.querySelector('input[name="UserName"]') || document.querySelector('input[type="text"]');
                let pwdInput = document.querySelector('input[name="LoginInput.Password"]') || document.querySelector('input[formcontrolname="password"]') || document.querySelector('input[type="password"]');
                let otpInput = document.querySelector('input[name="LoginInput.Otp"]') || document.querySelector('input.input-otp') || document.querySelector('input[formcontrolname="otp"]') || document.querySelector('input[placeholder*="OTP"]');

                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;

                if (acc && (user || !acc.value)) {
                    let u = user || acc.value;
                    if (u) {
                        nativeInputValueSetter.call(acc, u);
                        acc.dispatchEvent(new Event('input', { bubbles: true }));
                        acc.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }

                if (pwdInput && (pass || !pwdInput.value)) {
                    let p = pass || pwdInput.value;
                    if (p) {
                        nativeInputValueSetter.call(pwdInput, p);
                        pwdInput.dispatchEvent(new Event('input', { bubbles: true }));
                        pwdInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }

                if (otpInput && code) {
                    nativeInputValueSetter.call(otpInput, code);
                    otpInput.dispatchEvent(new Event('input', { bubbles: true }));
                    otpInput.dispatchEvent(new Event('change', { bubbles: true }));
                }

                let btn = document.querySelector('#kt_login_signin_submit') || document.querySelector('button[type="submit"]') || document.querySelector('.kt-login__btn-primary');
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
                """
                self.driver.execute_script(js, otp, user, pwd)
                
                import time
                for _ in range(16):
                    time.sleep(0.5)
                    st = self.get_status()
                    if st in ("AUTHENTICATED", "LOGIN_FAILED", "OTP_INVALID"):
                        return st
                return self.get_status()
            except Exception as e:
                logger.error(f"Error submitting OTP for {self.profile_name}: {e}")
                return self.get_status()

