import threading
import logging
import urllib.parse
from app.services.browser.browser_manager import BaseBrowserSession
from selenium.webdriver.common.by import By
from app.core.config import settings

logger = logging.getLogger(__name__)

class LongChauBrowserSession(BaseBrowserSession):
    def start(self, probe_only=False):
        super().start(probe_only)
        import time
        time.sleep(3) # Wait for Budibase redirect
        self.status = self.get_status()
        return self.status

    _instance = None
    _singleton_lock = threading.Lock()

    def __init__(self):
        self.cached_cookies = None
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
                if self.status == "AUTHENTICATED":
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

                
                # If we are on identity.fptshop or Microsoft login, it's OTP/Login
                if "identity.fptshop" in url or "identity.frt.vn" in url or "accounts.google" in url or "microsoft" in url:
                    page_source = self.driver.page_source.lower()
                    if "otp" in page_source or "mA xAc nh-n" in page_source or "mã xác nhận" in page_source:
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
                elif "bapp.frt.vn" in url and "login" in url:
                    self.status = "LOGIN_PAGE"
                    try:
                        self.driver.maximize_window()
                        # Switch to new tab if one opened
                        if len(self.driver.window_handles) > 1:
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                            url = self.driver.current_url.lower() # update url
                            
                        if "bapp.frt.vn" in self.driver.current_url.lower():
                            if not getattr(self, '_sso_clicked', False):
                                button = self.driver.find_element(By.XPATH, "//button[contains(., 'FRT OpenID')]")
                                self.driver.execute_script("arguments[0].click();", button)
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
                elif "frt-gscmr-long-chau" in url:

                    # We are in the app, check if we have the Budibase cookie
                    self.status = "AUTHENTICATED"
                    try: self.get_auth_cookies()
                    except: pass
                    if True:
                        import threading
                        def switch_headless():
                            try:
                                import time
                                time.sleep(1)
                                with self._lock:
                                    if self.driver:
                                        try: self.driver.quit()
                                        except: pass
                                        self.clear_driver()
                            except: pass
                        threading.Thread(target=switch_headless).start()
                else:
                    self.status = "UNKNOWN"
            except Exception as e:
                logger.error(f"Long Chau browser session lost: {e}")
                self.status = "STOPPED"
                self.clear_driver()
                
            return self.status

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
        """Extracts the budibase app ID from the URL or cookies if needed."""
        if not self.driver: return None
        # Usually not strictly needed for `/api/tables` if we have the cookie,
        # but let's see if we can extract it.
        return None
