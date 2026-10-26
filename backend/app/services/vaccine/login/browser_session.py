import threading
import logging
import urllib.parse
from app.services.browser.browser_manager import BaseBrowserSession
from selenium.webdriver.common.by import By
from app.core.config import settings

logger = logging.getLogger(__name__)

class VaccineBrowserSession(BaseBrowserSession):
    def start(self, probe_only=False, headless=False):
        self._sso_clicked = False
        self._closing_thread_started = False
        self._initial_probed = True
        self._auto_otp_attempted = False
        super().start(probe_only=probe_only, headless=headless)
        if getattr(self, '_needs_storage_clear', False) and self.driver:
            try:
                self.driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
                self.driver.delete_all_cookies()
                self._needs_storage_clear = False
                self.driver.get(self.start_url)
            except: pass
        if self.driver:
            import time
            time.sleep(3) # Wait for Budibase redirect
            self.status = self.get_status()

        return self.status

    _instance = None
    _singleton_lock = threading.Lock()

    def __init__(self):
        self.cached_cookies = None
        self.cached_headers = None
        self._needs_storage_clear = False
        super().__init__(
            profile_name="vaccine-profile",
            start_url=settings.VACCINE_LOGIN_URL
        )

    @classmethod
    def get_instance(cls):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = VaccineBrowserSession()
        return cls._instance

    def _is_on_target_page(self) -> bool:
        if not self.driver: return False
        return "frt-gscmr-vaccine" in self.driver.current_url.lower()

    def get_status(self) -> str:
        with self._lock:
            if self.driver is None:
                if self.status == "AUTHENTICATED" and self.cached_cookies and any(k in self.cached_cookies for k in ['budibase:auth', 'bb-auth']):
                    return self.status
                if self.status != "ERROR":
                    self.status = "STOPPED"
                return self.status

            try:
                # Always ensure we are on a valid window
                if len(self.driver.window_handles) > 0:
                    try:
                        self.driver.current_url
                    except:
                        # Current window closed, switch to the first one
                        self.driver.switch_to.window(self.driver.window_handles[0])
                else:
                    raise Exception('All windows closed')
                    
                url = self.driver.current_url.lower()

                cookies_dict = {}
                try:
                    cookies_dict = {c['name']: c['value'] for c in self.driver.get_cookies()}
                except: pass
                has_auth_cookie = any(k in cookies_dict for k in ['budibase:auth', 'bb-auth'])

                # Check for login pages
                if "identity.fptshop" in url or "identity.frt.vn" in url or "accounts.google" in url or "microsoft" in url:
                    try:
                        js = """
                        let pwd = document.querySelector('input[name="LoginInput.Password"]') || document.querySelector('input[formcontrolname="password"]') || document.querySelector('input[type="password"]');
                        let acc = document.querySelector('input[name="LoginInput.UserNameOrEmailAddress"]') || document.querySelector('input[formcontrolname="employee_code"]') || document.querySelector('input[name="UserName"]') || document.querySelector('input[type="text"]');
                        
                        let providedUser = arguments[0];
                        let providedPass = arguments[1];
                        
                        if (providedUser && providedPass && pwd && acc) {
                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            
                            nativeInputValueSetter.call(acc, providedUser);
                            acc.dispatchEvent(new Event('input', { bubbles: true }));
                            acc.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            nativeInputValueSetter.call(pwd, providedPass);
                            pwd.dispatchEvent(new Event('input', { bubbles: true }));
                            pwd.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            let btn = document.querySelector('#kt_login_signin_submit') || document.querySelector('button[type="submit"]') || document.querySelector('.kt-login__btn-primary');
                            if (btn && !window._vac_submitted) {
                                window._vac_submitted = true;
                                setTimeout(() => btn.click(), 400);
                            }
                        }
                        """
                        user = self.temp_creds.get("username") if getattr(self, "temp_creds", None) else ""
                        pwd = self.temp_creds.get("password") if getattr(self, "temp_creds", None) else ""
                        if user and pwd:
                            self.driver.execute_script(js, user, pwd)
                    except: pass
                    
                    page_source = self.driver.page_source.lower()
                    has_otp_field = False
                    try:
                        has_otp_field = bool(self.driver.find_elements(By.NAME, "LoginInput.Otp") or self.driver.find_elements(By.CLASS_NAME, "input-otp"))
                    except: pass

                    if has_otp_field or "vui lòng nhập mã otp" in page_source:
                        from app.core.totp import get_current_totp_code
                        auto_otp = get_current_totp_code()
                        if auto_otp and not getattr(self, "_auto_otp_attempted", False):
                            self._auto_otp_attempted = True
                            logger.info(f"[{self.profile_name}] Tự động lấy mã TOTP từ Authenticator Secret và submit...")
                            self.submit_otp(auto_otp)
                            return self.get_status()
                        self.status = "OTP_REQUIRED"
                        try: self.driver.maximize_window()
                        except: pass
                    elif "mã xác thực không hợp lệ" in page_source or "mã xác nhận không đúng" in page_source:
                        self.status = "OTP_INVALID"
                        try: self.driver.maximize_window()
                        except: pass
                    else:
                        self.status = "LOGIN_PAGE"
                        try: self.driver.maximize_window()
                        except: pass
                elif ("ptt-public.frt.vn" in url and "login" in url) or "auth/login" in url:
                    self.status = "LOGIN_PAGE"
                    try:
                        self.driver.maximize_window()
                        if len(self.driver.window_handles) > 1:
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                            url = self.driver.current_url.lower()
                            
                        if "ptt-public.frt.vn" in self.driver.current_url.lower():
                            if not getattr(self, '_sso_clicked', False):
                                buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'FPT Retail Account')]")
                                if buttons:
                                    self.driver.execute_script("arguments[0].click();", buttons[0])
                                    self._sso_clicked = True
                                    import time
                                    time.sleep(1)
                                    if len(self.driver.window_handles) > 1:
                                        self.driver.switch_to.window(self.driver.window_handles[-1])
                    except:
                        pass

                elif "builder/apps" in url:
                    self.status = "NAVIGATING"
                    try:
                        self.driver.get("https://ptt-public.frt.vn/app/frt-gscmr-vaccine#/ticket")
                    except:
                        pass
                elif "frt-gscmr-vaccine" in url:
                    if has_auth_cookie:
                        csrf_token = None
                        try:
                            csrf_token = self.driver.execute_script("return window.localStorage.getItem('csrf-token');")
                        except: pass
                        
                        self.status = "AUTHENTICATED"
                        self.cached_cookies = cookies_dict
                        
                        self.cached_headers = {
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                            "x-budibase-app-id": self.get_app_id(),
                            "x-csrf-token": csrf_token if csrf_token else ""
                        }
                        
                        def switch_headless():
                            try:
                                import time
                                time.sleep(1.0)
                                driver_to_quit = None
                                with self._lock:
                                    if self.driver:
                                        driver_to_quit = self.driver
                                        self.clear_driver()
                                if driver_to_quit:
                                    try: driver_to_quit.quit()
                                    except: pass
                            except: pass
                        if not getattr(self, '_closing_thread_started', False):
                            self._closing_thread_started = True
                            threading.Thread(target=switch_headless, daemon=True).start()
                    else:
                        # Page is still loading or rendering login modal
                        body_text = ""
                        try:
                            body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        except: pass
                        if "log in" in body_text or "đăng nhập" in body_text:
                            self.status = "LOGIN_PAGE"
                            try:
                                buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'FPT Retail Account')]")
                                if buttons and not getattr(self, '_sso_clicked', False):
                                    self.driver.execute_script("arguments[0].click();", buttons[0])
                                    self._sso_clicked = True
                            except: pass
                        else:
                            self.status = "NAVIGATING"
                else:
                    self.status = "UNKNOWN"
            except Exception as e:
                err_str = str(e).lower()
                if "invalid session id" in err_str or "not connected to devtools" in err_str:
                    logger.debug(f"Vaccine browser closed: {e}")
                elif self.status != "AUTHENTICATED":
                    logger.warning(f"Vaccine browser session lost: {e}")
                    self.status = "STOPPED"
                self.clear_driver()
                
            return self.status

    def get_auth_cookies(self):
        if getattr(self, "cached_cookies", None) and any(k in self.cached_cookies for k in ['budibase:auth', 'bb-auth']):
            return self.cached_cookies
        if not self.driver:
            return None
            
        cookies = {}
        for c in self.driver.get_cookies():
            cookies[c['name']] = c['value']
        if any(k in cookies for k in ['budibase:auth', 'bb-auth']):
            self.cached_cookies = cookies
            return cookies
        return None

    def get_app_id(self):
        return settings.VACCINE_APP_ID

    def get_auth_headers(self):
        if not getattr(self, "cached_headers", None):
            self.cached_headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "x-budibase-app-id": self.get_app_id(),
                "x-csrf-token": ""
            }
        return self.cached_headers

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

