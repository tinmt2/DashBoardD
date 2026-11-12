"""
Window Activator Service for Windows OS.
Manages identification, restoration, and foreground activation of managed Chrome application windows.

Implements safe Win32 desktop lifecycle:
- Dedicated single-use worker threads for desktop switching (never on pooled or FastAPI threads).
- Explicit error checking and access right validation.
- Guaranteed handle cleanup in finally blocks.
- Clean Win32 API calls without keyboard emulation hacks.
"""

import os
import sys
import time
import queue
import logging
import threading
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Constants for Windows Win32 API
SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_MAXIMIZE = 3
SW_SHOWNOACTIVATE = 4
SW_SHOW = 5
SW_MINIMIZE = 6
SW_SHOWMINNOACTIVE = 7
SW_SHOWNA = 8
SW_RESTORE = 9

# Desktop specific access rights
DESKTOP_READOBJECTS = 0x0001
DESKTOP_WRITEOBJECTS = 0x0080
DESKTOP_ENUMERATE = 0x0040
DESKTOP_ALL_DEFAULT = 0x01FF


def get_managed_chrome_pids(chromedriver_pid: Optional[int] = None, profile_dir: Optional[str] = None) -> List[int]:
    """
    Identifies the exact Main Chrome Process IDs (PID) belonging to the managed session.
    Filters out background utility/gpu/crashpad/renderer child processes.
    """
    pids: List[int] = []
    
    try:
        import psutil
    except ImportError:
        logger.warning("psutil is not installed; cannot inspect child process trees.")
        return pids

    # 1. Inspect direct and descendant children of chromedriver.exe
    if chromedriver_pid:
        try:
            parent = psutil.Process(chromedriver_pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    name = child.name().lower()
                    if "chrome" in name:
                        cmd = " ".join(child.cmdline() or [])
                        # Main browser process does not have '--type='
                        if "--type=" not in cmd:
                            if child.pid not in pids:
                                pids.append(child.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            logger.debug(f"Chromedriver PID {chromedriver_pid} not found in process table.")

    # 2. Fallback: Search system processes by profile directory path
    if not pids and profile_dir:
        try:
            norm_profile = os.path.normcase(os.path.abspath(profile_dir))
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = (proc.info.get('name') or '').lower()
                    if "chrome" in name:
                        cmd = " ".join(proc.info.get('cmdline') or [])
                        if norm_profile in os.path.normcase(cmd) and "--type=" not in cmd:
                            pid = proc.info.get('pid')
                            if pid and pid not in pids:
                                pids.append(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug(f"Error scanning processes by profile_dir: {e}")

    return pids


def find_window_for_pids(pids: List[int]) -> Optional[Tuple[int, str, str]]:
    """
    Locates the top-level Chrome application window (HWND) belonging to the given PIDs.
    Scans accessible desktops in the current Window Station (prioritizing 'Default').
    Returns tuple: (hwnd, desktop_name, window_title) or None.
    """
    if sys.platform != "win32" or not pids:
        return None

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    desktops: List[str] = []
    try:
        hwinsta = user32.GetProcessWindowStation()
        def enum_desktop_cb(name: Optional[str], lparam: wintypes.LPARAM) -> bool:
            if name:
                desktops.append(name)
            return True

        DESKTOPENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, ctypes.c_wchar_p, wintypes.LPARAM)
        user32.EnumDesktopsW(hwinsta, DESKTOPENUMPROC(enum_desktop_cb), 0)
    except Exception as e:
        logger.debug(f"Failed to enumerate desktops: {e}")

    # Prioritize 'Default' interactive desktop
    ordered_desktops: List[str] = []
    if "Default" in desktops:
        ordered_desktops.append("Default")
    for d in desktops:
        if d not in ordered_desktops:
            ordered_desktops.append(d)

    if not ordered_desktops:
        ordered_desktops = ["Default"]

    target_pid_set = set(pids)
    matching_windows: List[Tuple[int, str, str]] = []

    for dname in ordered_desktops:
        # Request read and enumerate rights for safe discovery
        hdesk = user32.OpenDesktopW(dname, 0, False, DESKTOP_READOBJECTS | DESKTOP_ENUMERATE)
        if not hdesk:
            continue

        try:
            def enum_win_cb(hwnd: wintypes.HWND, lparam: wintypes.LPARAM) -> bool:
                try:
                    pid = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value in target_pid_set:
                        cls_buf = ctypes.create_unicode_buffer(256)
                        user32.GetClassNameW(hwnd, cls_buf, 256)
                        class_name = cls_buf.value.lower()
                        
                        if "widgetwin_1" in class_name:
                            rect = wintypes.RECT()
                            user32.GetWindowRect(hwnd, ctypes.byref(rect))
                            width = rect.right - rect.left
                            height = rect.bottom - rect.top
                            if width > 50 and height > 50:
                                length = user32.GetWindowTextLengthW(hwnd)
                                buf = ctypes.create_unicode_buffer(length + 1)
                                user32.GetWindowTextW(hwnd, buf, length + 1)
                                matching_windows.append((int(hwnd), dname, buf.value))
                except Exception:
                    pass
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumDesktopWindows(hdesk, WNDENUMPROC(enum_win_cb), 0)
        finally:
            user32.CloseDesktop(hdesk)

        if matching_windows:
            break

    if matching_windows:
        for item in matching_windows:
            if "zalo" in item[2].lower():
                return item
        return matching_windows[0]

    return None


def activate_window(hwnd: int, target_pid: int, desktop_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Restores the window if minimized and requests Windows to activate it to the foreground.
    
    SAFETY PROTOCOL:
    - Runs in a dedicated single-use worker thread to isolate SetThreadDesktop from shared threads.
    - Validates desktop handle opening and error codes.
    - Ensures CloseDesktop is called in finally blocks.
    - Uses pure Win32 activation without global keyboard simulation.
    """
    if sys.platform != "win32":
        return {
            "success": True,
            "activated": False,
            "action": "unsupported_platform",
            "message": "Window activation is only supported on Windows.",
            "hwnd": hwnd
        }

    res_queue: queue.Queue = queue.Queue()

    def _win32_activation_worker():
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        hdesk = None
        try:
            # If a specific desktop was identified, switch the worker thread to that desktop
            if desktop_name:
                access_mask = DESKTOP_READOBJECTS | DESKTOP_WRITEOBJECTS | DESKTOP_ENUMERATE
                hdesk = user32.OpenDesktopW(desktop_name, 0, False, access_mask)
                if not hdesk:
                    # Fallback with standard rights
                    hdesk = user32.OpenDesktopW(desktop_name, 0, False, DESKTOP_ALL_DEFAULT)
                
                if not hdesk:
                    err_code = kernel32.GetLastError()
                    logger.warning(f"Failed to OpenDesktopW('{desktop_name}'): error={err_code}")
                    res_queue.put({
                        "success": False,
                        "activated": False,
                        "action": "desktop_open_failed",
                        "message": f"Không thể mở desktop '{desktop_name}' (mã lỗi {err_code}).",
                        "hwnd": hwnd
                    })
                    return

                set_ok = user32.SetThreadDesktop(hdesk)
                if not set_ok:
                    err_code = kernel32.GetLastError()
                    logger.warning(f"Failed to SetThreadDesktop: error={err_code}")
                    res_queue.put({
                        "success": False,
                        "activated": False,
                        "action": "desktop_set_failed",
                        "message": f"Không thể gán desktop '{desktop_name}' cho luồng xử lý (mã lỗi {err_code}).",
                        "hwnd": hwnd
                    })
                    return

            # Check if HWND is valid on the active desktop
            if not user32.IsWindow(hwnd):
                res_queue.put({
                    "success": False,
                    "activated": False,
                    "action": "invalid_hwnd",
                    "message": "Cửa sổ không tồn tại hoặc đã bị đóng.",
                    "hwnd": hwnd
                })
                return

            # Step 1: Restore if minimized, or ensure shown
            is_minimized = bool(user32.IsIconic(hwnd))
            if is_minimized:
                user32.ShowWindow(hwnd, SW_RESTORE)
            else:
                user32.ShowWindow(hwnd, SW_SHOW)

            # Step 2: Grant foreground permission and request foreground transition
            try:
                user32.AllowSetForegroundWindow(target_pid)
            except Exception:
                pass

            user32.BringWindowToTop(hwnd)
            fg_success = bool(user32.SetForegroundWindow(hwnd))

            # Step 3: Verify resulting state
            time.sleep(0.05)
            current_fg = user32.GetForegroundWindow()
            is_now_iconic = bool(user32.IsIconic(hwnd))

            if current_fg == hwnd:
                res_queue.put({
                    "success": True,
                    "activated": True,
                    "action": "foreground",
                    "message": "Cửa sổ Zalo đã được đưa lên phía trước màn hình.",
                    "hwnd": hwnd
                })
            elif not is_now_iconic:
                res_queue.put({
                    "success": True,
                    "activated": True,
                    "action": "restored",
                    "message": "Cửa sổ Zalo đã được khôi phục hiển thị trên màn hình.",
                    "hwnd": hwnd
                })
            else:
                res_queue.put({
                    "success": False,
                    "activated": False,
                    "action": "focus_refused",
                    "message": "Windows từ chối cấp tiêu điểm foreground cho cửa sổ Zalo.",
                    "hwnd": hwnd
                })

        except Exception as e:
            logger.error(f"Unexpected error in _win32_activation_worker: {e}", exc_info=True)
            res_queue.put({
                "success": False,
                "activated": False,
                "action": "worker_exception",
                "message": f"Lỗi nội bộ khi thao tác cửa sổ Win32: {str(e)}",
                "hwnd": hwnd
            })
        finally:
            if hdesk:
                try:
                    user32.CloseDesktop(hdesk)
                except Exception as e:
                    logger.debug(f"Error closing desktop handle: {e}")

    # Run activation in dedicated thread with timeout
    worker_thread = threading.Thread(target=_win32_activation_worker, name="ZaloWin32Activator", daemon=True)
    worker_thread.start()
    worker_thread.join(timeout=4.0)

    try:
        return res_queue.get_nowait()
    except queue.Empty:
        logger.error(f"Win32 activation worker thread timed out for HWND={hwnd}")
        return {
            "success": False,
            "activated": False,
            "action": "timeout",
            "message": "Thao tác kích hoạt cửa sổ quá thời gian chờ (timeout).",
            "hwnd": hwnd
        }


def activate_zalo_window(driver: Any, profile_dir: str) -> Dict[str, Any]:
    """
    Coordinates finding and bringing the managed Zalo Chrome application window to the foreground.
    """
    chromedriver_pid: Optional[int] = None
    if driver:
        try:
            service = getattr(driver, "service", None)
            process = getattr(service, "process", None)
            if process and hasattr(process, "pid"):
                chromedriver_pid = process.pid
        except Exception:
            pass

    pids = get_managed_chrome_pids(chromedriver_pid=chromedriver_pid, profile_dir=profile_dir)
    if not pids:
        logger.warning(f"Could not locate main Chrome process for chromedriver_pid={chromedriver_pid}, profile_dir={profile_dir}")
        return {
            "success": False,
            "activated": False,
            "action": "no_process",
            "message": "Không tìm thấy tiến trình Chrome của Zalo Web."
        }

    win_info = find_window_for_pids(pids)
    if not win_info:
        logger.warning(f"No Chrome_WidgetWin_1 window found for PIDs: {pids}")
        return {
            "success": False,
            "activated": False,
            "action": "no_window",
            "message": "Không tìm thấy cửa sổ giao diện Zalo trên Windows."
        }

    hwnd, dname, title = win_info
    logger.info(f"Activating Zalo window HWND={hwnd} on desktop='{dname}', title='{title}'")
    return activate_window(hwnd, pids[0], desktop_name=dname)
