import os
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import subprocess

# Global lock per profile to prevent concurrent Chrome launches
_profile_locks = {}
_global_lock = threading.Lock()

def get_profile_lock(profile_name):
    with _global_lock:
        if profile_name not in _profile_locks:
            _profile_locks[profile_name] = threading.RLock()
        return _profile_locks[profile_name]

logger = logging.getLogger(__name__)

_active_profiles_refs = {} # profile_name -> list of instances

def acquire_profile(profile_name, instance):
    with _global_lock:
        refs = _active_profiles_refs.get(profile_name, [])
        if instance not in refs:
            refs.append(instance)
        _active_profiles_refs[profile_name] = refs

def release_profile(profile_name, instance):
    with _global_lock:
        refs = _active_profiles_refs.get(profile_name, [])
        if instance in refs:
            refs.remove(instance)
        _active_profiles_refs[profile_name] = refs

def is_profile_in_use_by_others(profile_name, instance):
    with _global_lock:
        refs = _active_profiles_refs.get(profile_name, [])
        return any(ref is not instance and ref.driver is not None for ref in refs)


class BaseBrowserSession:
    """
    Generic Base Browser Session Manager.
    Responsible for Chrome profile lifecycle, window management, and singleton patterns.
    """
    def __init__(self, profile_name: str, start_url: str):
        self.profile_name = profile_name
        self.start_url = start_url
        self.driver = None
        self.status = "STOPPED"
        self.is_headless = False
        self._lock = threading.RLock()

    def _cleanup_orphaned_processes(self, profile_path: str):
        try:
            if os.name == 'nt':
                # Windows process cleanup
                output = subprocess.check_output('wmic process where "name=\'chrome.exe\'" get commandline,processid', shell=True).decode('utf-8', errors='ignore')
                for line in output.splitlines():
                    if self.profile_name in line:
                        parts = line.strip().split()
                        pid = parts[-1]
                        if pid.isdigit():
                            logger.info(f"Killing orphaned Chrome process for {self.profile_name}: {pid}")
                            subprocess.call(['taskkill', '/F', '/PID', pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Linux process cleanup
                subprocess.call(f"pkill -f '{self.profile_name}'", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Also clean up the lockfile if it still exists
            lock_file = os.path.join(profile_path, "lockfile")
            if os.path.exists(lock_file):
                os.remove(lock_file)
                
            # Reset exit_type to Normal in Preferences file if present to eliminate "Restore pages?" bubble
            pref_file = os.path.join(profile_path, "Default", "Preferences")
            if os.path.exists(pref_file):
                try:
                    import json
                    with open(pref_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "profile" in data:
                        data["profile"]["exit_type"] = "Normal"
                        data["profile"]["exited_cleanly"] = True
                        with open(pref_file, "w", encoding="utf-8") as f:
                            json.dump(data, f)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error cleaning up orphaned processes for {self.profile_name}: {e}")

    def start(self, probe_only=False, headless=False):
        import time
        with get_profile_lock(self.profile_name), self._lock:
            effective_headless = probe_only or headless or (os.name != 'nt' and not os.environ.get("DISPLAY"))
            if probe_only and self.driver is None:
                # If we probed recently (within 30 seconds), don't probe again to avoid jumping Chrome!
                if time.time() - getattr(self, 'last_probe_time', 0) < 30:
                    return self.status if self.status == "AUTHENTICATED" else "STOPPED"
                self.last_probe_time = time.time()
                
            if self.driver is None and is_profile_in_use_by_others(self.profile_name, self):
                logger.info(f"Profile {self.profile_name} is currently used by another session. Yielding...")
                self.status = "STARTING"
                return self.status
                
            if self.driver is not None:
                # If we want a visible browser but currently have a headless one, we MUST restart it!
                if not effective_headless and getattr(self, 'is_headless', False):
                    logger.info(f"Restarting headless session to visible for {self.profile_name}")
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                else:
                    try:
                        # Reuse existing driver and ensure it's on the right page
                        if len(self.driver.window_handles) > 1:
                            # Close other tabs if any
                            for handle in self.driver.window_handles[1:]:
                                self.driver.switch_to.window(handle)
                                self.driver.close()
                        
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        # Delegate the check to subclass
                        if not self._is_on_target_page():
                            self.driver.get(self.start_url)
                        
                        self.status = self.get_status()
                        if probe_only:
                            try:
                                self.driver.quit()
                            except Exception:
                                pass
                            self.clear_driver()
                        return self.status
                    except Exception as e:
                        logger.error(f"Failed to reuse existing session for {self.profile_name}: {e}")
                        self.driver = None
                        self.status = "STOPPED"
                        self.is_headless = False
                        # Fall through to create a new session
                
            self.status = "STARTING"
            try:
                options = Options()
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--remote-debugging-port=0")
                options.add_argument("--disable-session-crashed-bubble")
                options.add_argument("--hide-crash-restore-bubble")
                options.add_argument("--disable-features=InfiniteSessionRestore")
                if effective_headless:
                    options.add_argument("--headless=new")
                
                # Create a specific profile directory
                profile_path = os.path.abspath(os.path.join(os.getcwd(), ".browser", self.profile_name))
                options.add_argument(f"user-data-dir={profile_path}")
                
                # Enable Password Manager in Chrome & avoid crash restore prompts
                prefs = {
                    "credentials_enable_service": True,
                    "profile.password_manager_enabled": True,
                    "profile.exit_type": "Normal",
                    "profile.exited_cleanly": True
                }
                options.add_experimental_option("prefs", prefs)
                
                # Remove automation warnings
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                
                self._cleanup_orphaned_processes(profile_path)
                
                self.driver = webdriver.Chrome(options=options)
                acquire_profile(self.profile_name, self)
                self.is_headless = effective_headless
                
                try:
                    if effective_headless or self.profile_name == "fpt-shop-profile":
                        self.driver.minimize_window()
                    else:
                        self.driver.maximize_window()
                except:
                    pass
                
                self.driver.get(self.start_url)
                self.status = self.get_status()
                
                if probe_only:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.clear_driver()
            except Exception as e:
                logger.error(f"Failed to start browser session for {self.profile_name}: {e}")
                self.status = "ERROR"
                self.driver = None
                
            return self.status

    def _is_on_target_page(self) -> bool:
        """Override in subclass to determine if driver is on the expected start/report URL."""
        return self.start_url.lower() in self.driver.current_url.lower()

    def get_status(self) -> str:
        """Override in subclass to implement domain-specific login detection logic."""
        raise NotImplementedError("Subclass must implement get_status")

    def stop(self):
        with self._lock:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.error(f"Error stopping browser session for {self.profile_name}: {e}")
                self.driver = None
            release_profile(self.profile_name, self)
            self.status = "STOPPED"
            self.is_headless = False

    def clear_driver(self):
        self.driver = None
        release_profile(self.profile_name, self)
