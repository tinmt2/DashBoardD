from __future__ import annotations
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

def kill_processes_using_profile(profile_path: str):
    """Tìm và tắt triệt để các tiến trình Chrome hoặc Chromedriver bị treo đang giữ profile."""
    if not profile_path:
        return
    try:
        import psutil
        norm_keyword = os.path.basename(os.path.abspath(profile_path)).lower()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pname = (proc.info.get('name') or '').lower()
                if 'chrome' in pname or 'chromedriver' in pname:
                    cmd = ' '.join(proc.info.get('cmdline') or []).lower()
                    if norm_keyword in cmd:
                        proc.kill()
            except Exception:
                continue
    except Exception:
        # Fallback PowerShell nếu không có psutil
        try:
            norm_path = os.path.abspath(profile_path).replace("\\", "\\\\")
            ps_cmd = f'Get-CimInstance Win32_Process | Where-Object {{ ($_.Name -like "*chrome*") -and ($_.CommandLine -like "*{norm_path}*") }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}'
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=5)
        except Exception:
            pass

def cleanup_chrome_sessions(profile_path: str | None = None):
    if profile_path:
        profile_dir = os.path.abspath(profile_path)
        kill_processes_using_profile(profile_dir)
        
        # Xóa toàn bộ file lock bao gồm SingletonLock, LOCK, lockfile
        for root, dirs, files in os.walk(profile_dir):
            for f in files:
                if f in ("LOCK", "SingletonLock", "lockfile") or "lock" in f.lower():
                    try:
                        os.remove(os.path.join(root, f))
                    except Exception:
                        pass

def get_bundled_driver_path() -> str | None:
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).resolve().parent.parent.parent
    
    driver_path = base_dir / 'chromedriver.exe'
    if driver_path.exists():
        return str(driver_path)
    return None

def create_chrome_driver(
    profile_path: str | None = None,
    headless: bool = False,
    use_manager: bool = False,
    detach: bool = False,
    start_maximized: bool = True,
    app_url: str | None = None,
    incognito: bool = True,
    isolated_profile: bool = False,
) -> webdriver.Chrome:
    if profile_path:
        cleanup_chrome_sessions(profile_path)

    options = ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    if detach:
        options.add_experimental_option("detach", True)

    if app_url:
        options.add_argument(f"--app={app_url}")
    elif start_maximized:
        options.add_argument("--start-maximized")

    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-search-engine-choice-screen")
    
    # Tối ưu giảm bớt các tiến trình ngầm (utility processes) của Chromium
    options.add_argument("--renderer-process-limit=1")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-default-apps")
    options.add_argument("--mute-audio")
    
    options.add_argument("--disable-features=BlockInsecurePrivateNetworkRequests")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--ignore-certificate-errors")
    
    options.set_capability("unhandledPromptBehavior", "accept")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    
    if incognito:
        options.add_argument("--incognito")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--window-position=-32000,-32000")
        options.add_argument("--disable-gpu")

    if isolated_profile:
        temp_dir = tempfile.mkdtemp(prefix="ftel_autologin_")
        options.add_argument(f"--user-data-dir={temp_dir}")
        options.add_argument("--disable-web-security")
    elif profile_path:
        options.add_argument(f"--user-data-dir={profile_path}")

    bundled_path = get_bundled_driver_path()
    if bundled_path and os.path.exists(bundled_path):
        try:
            service = ChromeService(executable_path=bundled_path)
            return webdriver.Chrome(service=service, options=options)
        except Exception:
            pass

    try:
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=options)
        if bundled_path and hasattr(driver, "service") and getattr(driver.service, "path", None):
            try:
                import shutil
                if os.path.abspath(driver.service.path) != os.path.abspath(bundled_path):
                    shutil.copy2(driver.service.path, bundled_path)
            except Exception:
                pass
        return driver
    except Exception as e:
        raise RuntimeError(f"Không thể khởi động trình duyệt Chrome/Chromedriver: {e}") from e
