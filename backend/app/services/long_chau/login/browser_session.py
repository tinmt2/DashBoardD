import threading
import logging
import urllib.parse
from app.services.browser.browser_manager import BaseBrowserSession
from selenium.webdriver.common.by import By
from app.core.config import settings

logger = logging.getLogger(__name__)

class LongChauBrowserSession(BaseBrowserSession):
    def start(self, probe_only=False, headless=False):
        self._sso_clicked = False
        self._closing_thread_started = False
        self._initial_probed = True
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
        self.temp_creds = None
        super().__init__(
            profile_name="fpt-sso-profile",
            start_url=settings.LONG_CHAU_LOGIN_URL
        )

    @classmethod
    def get_instance(cls):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = LongChauBrowserSession()
        return cls._instance

    def _is_on_target_page(self) -> bool:
        if not self.driver: return False
        return "frt-gscmr-long-chau" in self.driver.current_url.lower()

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

                # 1. Identity / SSO login page (auto-fill credentials if provided, detect OTP)
                if "identity.fptshop" in url or "identity.frt.vn" in url or "accounts.google" in url or "microsoft" in url:
                    try:
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
                    except: pass

                    page_source = self.driver.page_source.lower()
                    if "otp" in page_source or "mã xác nhận" in page_source or "ma xac nhan" in page_source:
                        self.status = "OTP_REQUIRED"
                        try:
                            self.driver.maximize_window()
                        except:
                            pass
                    else:
                        self.status = "LOGIN_PAGE"
                        try:
                            self.driver.maximize_window()
                        except:
                            pass

                # 2. Budibase login page
                elif ("bapp.frt.vn" in url and "login" in url) or "auth/login" in url:
                    self.status = "LOGIN_PAGE"
                    try:
                        self.driver.maximize_window()
                        # Switch to new tab if one opened
                        if len(self.driver.window_handles) > 1:
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                            url = self.driver.current_url.lower()
                            
                        if "bapp.frt.vn" in self.driver.current_url.lower():
                            if not getattr(self, '_sso_clicked', False):
                                buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'FRT OpenID') or contains(., 'OpenID') or contains(., 'FPT Retail')] | //*[contains(text(), 'FRT OpenID') or contains(text(), 'FPT Retail Account')]")
                                if buttons:
                                    self.driver.execute_script("arguments[0].click();", buttons[0])
                                    self._sso_clicked = True
                                    import time
                                    time.sleep(1) # wait for tab to open
                                    if len(self.driver.window_handles) > 1:
                                        self.driver.switch_to.window(self.driver.window_handles[-1])
                    except:
                        pass

                elif "builder/apps" in url:
                    self.status = "NAVIGATING"
                    try:
                        self.driver.get("https://bapp.frt.vn/app/frt-gscmr-long-chau#/ticket")
                    except:
                        pass

                # 3. Inside the app URL (strictly verify actual auth cookie)
                elif "frt-gscmr-long-chau" in url:
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
                        # Page is still loading or rendering login modal inside the app
                        body_text = ""
                        try:
                            body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        except: pass
                        if "log in" in body_text or "đăng nhập" in body_text or "sign in" in body_text or "session" in body_text:
                            self.status = "LOGIN_PAGE"
                            try:
                                self.driver.maximize_window()
                                buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'FRT OpenID') or contains(., 'OpenID') or contains(., 'FPT Retail')] | //*[contains(text(), 'FRT OpenID') or contains(text(), 'FPT Retail Account')]")
                                if buttons and not getattr(self, '_sso_clicked', False):
                                    self.driver.execute_script("arguments[0].click();", buttons[0])
                                    self._sso_clicked = True
                                    import time
                                    time.sleep(1)
                                    if len(self.driver.window_handles) > 1:
                                        self.driver.switch_to.window(self.driver.window_handles[-1])
                            except: pass
                        else:
                            self.status = "NAVIGATING"
                else:
                    self.status = "UNKNOWN"
            except Exception as e:
                if self.status != "AUTHENTICATED":
                    logger.error(f"Long Chau browser session lost: {e}")
                    self.status = "STOPPED"
                self.clear_driver()
                
            return self.status

    def get_auth_headers(self):
        return self.cached_headers

    def get_auth_cookies(self):
        """Returns cookies formatted for the requests library."""
        if self.status != "AUTHENTICATED":
            return None
        
        if getattr(self, "cached_cookies", None):
            return self.cached_cookies
            
        if not self.driver:
            return None
            
        cookies = {}
        for c in self.driver.get_cookies():
            cookies[c['name']] = c['value']
        self.cached_cookies = cookies
        return cookies

    def get_app_id(self):
        return "frt-gscmr-long-chau"
