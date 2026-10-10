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
        
    @classmethod
    def get_instance(cls):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = FPTBrowserSession()
        return cls._instance

    def _is_on_target_page(self) -> bool:
        if not self.driver: return False
        url = self.driver.current_url.lower()
        if "calllog.fptshop.com.vn/report/debtconfirm" in url:
            return True
        if "identity.fptshop.com.vn" in url or "accounts.google.com" in url or "microsoftonline.com" in url:
            # We are in the auth flow, do not redirect
            return True
        return False

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
                    if self.status != "AUTHENTICATED":
                        pass # Removed minimize_window
                    self.status = "AUTHENTICATED"
                    if not getattr(self, "is_headless", True):
                        import threading
                        def switch_headless():
                            try:
                                import time
                                time.sleep(1)
                                with self._lock:
                                    if self.driver:
                                        try: self.driver.quit()
                                        except: pass
                                        self.driver = None
                            except: pass
                        threading.Thread(target=switch_headless).start()
                    
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
                        try:
                            self._force_show_window()
                        except:
                            pass
                    else:
                        self.status = "LOGIN_PAGE"

                elif "accounts.google.com" in url or "login.microsoftonline.com" in url:
                    self.status = "OTP_REQUIRED"
                    try:
                        self._force_show_window()
                    except:
                        pass
                else:
                    self.status = "UNKNOWN"
                    try:
                        self._force_show_window()
                    except:
                        pass
                        
            except Exception as e:
                logger.error(f"FPT browser session lost: {e}")
                self.status = "STOPPED"
                self.driver = None
                
            return self.status
