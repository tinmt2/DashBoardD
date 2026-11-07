import os
import json
import logging
import threading
from selenium.webdriver.common.by import By
from app.services.browser.browser_manager import BaseBrowserSession

logger = logging.getLogger(__name__)

DEFAULT_SHAREPOINT_URL = (
    "https://fptsoftware362.sharepoint.com/:x:/r/sites/FRT.ICT.HO/VHShop/GSCMR/"
    "_layouts/15/doc2.aspx?sourcedoc=%7B46906C5B-21C1-4B24-898F-79A7CAB20B3D%7D"
    "&file=1.%20LLV%20T11%202026.xlsx&action=default&mobileredirect=true"
)

class SharePointBrowserSession(BaseBrowserSession):
    _instance = None
    _singleton_lock = threading.Lock()

    def __init__(self):
        super().__init__(
            profile_name="sharepoint-profile",
            start_url=DEFAULT_SHAREPOINT_URL
        )
        self.last_authenticated_time = None
        self.cached_user = None

    @classmethod
    def get_instance(cls):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = SharePointBrowserSession()
        return cls._instance

    def _get_cookies_path(self) -> str:
        from app.core.config import BROWSER_DATA_DIR
        return os.path.join(BROWSER_DATA_DIR, "sharepoint-profile_cookies.json")

    def _save_cookies_to_disk(self):
        try:
            if not self.driver:
                return
            cookies = self.driver.get_cookies()
            if cookies:
                path = self._get_cookies_path()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=2)
                logger.info(f"Saved {len(cookies)} SharePoint session cookies to disk.")
        except Exception as e:
            logger.warning(f"Could not save SharePoint cookies: {e}")

    def has_stored_cookies(self) -> bool:
        path = self._get_cookies_path()
        return os.path.exists(path) and os.path.getsize(path) > 10

    def _is_on_target_page(self) -> bool:
        if not self.driver:
            return False
        url = self.driver.current_url.lower()
        if "login.microsoftonline.com" in url or "login.live.com" in url:
            return False
        return "sharepoint.com" in url

    def get_status(self) -> str:
        with self._lock:
            if self.driver is None:
                if self.status == "AUTHENTICATED":
                    return self.status
                if self.has_stored_cookies():
                    return "AUTHENTICATED"
                if self.status != "ERROR":
                    self.status = "STOPPED"
                return self.status

            try:
                url = self.driver.current_url.lower()

                # Check if on Microsoft login or SSO redirect
                if "login.microsoftonline.com" in url or "login.live.com" in url or "/_forms/" in url or "signin" in url:
                    self.status = "LOGIN_REQUIRED"
                    return self.status

                # If on SharePoint domain and not a login page
                if "sharepoint.com" in url and "login" not in url:
                    # Check if page is loaded
                    self.status = "AUTHENTICATED"
                    self._save_cookies_to_disk()
                    return self.status

                return self.status
            except Exception as e:
                logger.warning(f"Error checking SharePoint status: {e}")
                return self.status

    def start_login(self, target_url: str = None) -> str:
        """Launches a visible browser window for Microsoft 365 / SharePoint authentication."""
        with self._lock:
            if target_url:
                self.start_url = target_url
            status = self.start(probe_only=False, headless=False)
            if self.driver:
                try:
                    self.driver.maximize_window()
                except Exception:
                    pass
            return status

    def open_schedule_url(self, url: str) -> bool:
        """Navigates the current browser session to a specified SharePoint schedule URL."""
        with self._lock:
            if not self.driver:
                self.start_url = url
                self.start(probe_only=False, headless=False)
                return True
            try:
                self.driver.get(url)
                try:
                    self.driver.maximize_window()
                except Exception:
                    pass
                return True
            except Exception as e:
                logger.error(f"Error opening SharePoint URL: {e}")
                return False

    def logout(self):
        """Clears stored cookies and stops browser session."""
        with self._lock:
            try:
                cookies_path = self._get_cookies_path()
                if os.path.exists(cookies_path):
                    os.remove(cookies_path)
            except Exception as e:
                logger.warning(f"Error removing cookies file: {e}")

            if self.driver:
                try:
                    self.driver.get("https://login.microsoftonline.com/logout.srf")
                    import time
                    time.sleep(1)
                    self.driver.quit()
                except Exception:
                    pass
                self.clear_driver()
            self.status = "STOPPED"
