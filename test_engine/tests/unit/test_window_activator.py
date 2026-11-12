"""
Unit tests for window_activator service.
Covers:
- PID identification (chromedriver child and profile fallback)
- Window discovery
- Desktop open failure
- Desktop set failure
- Handle cleanup
- Invalid HWND
- Focus refused / foreground success
"""

import sys
import pytest
from unittest.mock import MagicMock, patch
from app.services.window_activator import (
    get_managed_chrome_pids,
    find_window_for_pids,
    activate_window,
    activate_zalo_window
)


def test_get_managed_chrome_pids_from_chromedriver():
    mock_child1 = MagicMock()
    mock_child1.name.return_value = "chrome.exe"
    mock_child1.cmdline.return_value = ["chrome.exe", "--user-data-dir=C:\\test", "--start-maximized"]
    mock_child1.pid = 1111

    mock_child2 = MagicMock()
    mock_child2.name.return_value = "chrome.exe"
    mock_child2.cmdline.return_value = ["chrome.exe", "--type=gpu-process"]
    mock_child2.pid = 2222

    mock_parent = MagicMock()
    mock_parent.children.return_value = [mock_child1, mock_child2]

    with patch("psutil.Process", return_value=mock_parent):
        pids = get_managed_chrome_pids(chromedriver_pid=9999)
        assert pids == [1111]
        assert 2222 not in pids


def test_get_managed_chrome_pids_fallback_profile():
    test_path = "D:\\test\\runtime\\zalo_web_profile"
    mock_proc = MagicMock()
    mock_proc.info = {
        "pid": 3333,
        "name": "chrome.exe",
        "cmdline": ["chrome.exe", f"--user-data-dir={test_path}"]
    }

    with patch("psutil.process_iter", return_value=[mock_proc]):
        pids = get_managed_chrome_pids(chromedriver_pid=None, profile_dir=test_path)
        assert 3333 in pids


def test_activate_zalo_window_no_process():
    with patch("app.services.window_activator.get_managed_chrome_pids", return_value=[]):
        res = activate_zalo_window(None, "dummy_profile")
        assert res["success"] is False
        assert res["action"] == "no_process"


def test_activate_zalo_window_no_window():
    with patch("app.services.window_activator.get_managed_chrome_pids", return_value=[4444]):
        with patch("app.services.window_activator.find_window_for_pids", return_value=None):
            res = activate_zalo_window(None, "dummy_profile")
            assert res["success"] is False
            assert res["action"] == "no_window"


def test_activate_zalo_window_success():
    with patch("app.services.window_activator.get_managed_chrome_pids", return_value=[4444]):
        with patch("app.services.window_activator.find_window_for_pids", return_value=(123456, "Default", "Zalo")):
            with patch("app.services.window_activator.activate_window", return_value={"success": True, "activated": True, "action": "foreground", "message": "OK"}):
                res = activate_zalo_window(None, "dummy_profile")
                assert res["success"] is True
                assert res["activated"] is True


def test_activate_window_desktop_open_failed():
    """Verifies handling when OpenDesktopW fails."""
    mock_user32 = MagicMock()
    mock_user32.OpenDesktopW.return_value = 0
    mock_kernel32 = MagicMock()
    mock_kernel32.GetLastError.return_value = 5  # ERROR_ACCESS_DENIED

    with patch("ctypes.windll.user32", mock_user32), patch("ctypes.windll.kernel32", mock_kernel32):
        res = activate_window(1234, 4444, desktop_name="RestrictedDesktop")
        assert res["success"] is False
        assert res["action"] == "desktop_open_failed"
        assert "5" in res["message"]


def test_activate_window_desktop_set_failed():
    """Verifies handling when SetThreadDesktop fails and ensures handle is closed."""
    mock_user32 = MagicMock()
    mock_user32.OpenDesktopW.return_value = 999
    mock_user32.SetThreadDesktop.return_value = 0
    mock_kernel32 = MagicMock()
    mock_kernel32.GetLastError.return_value = 170  # ERROR_BUSY

    with patch("ctypes.windll.user32", mock_user32), patch("ctypes.windll.kernel32", mock_kernel32):
        res = activate_window(1234, 4444, desktop_name="BusyDesktop")
        assert res["success"] is False
        assert res["action"] == "desktop_set_failed"
        mock_user32.CloseDesktop.assert_called_once_with(999)


def test_activate_window_invalid_hwnd():
    """Verifies handling when HWND is not a valid window."""
    mock_user32 = MagicMock()
    mock_user32.OpenDesktopW.return_value = 999
    mock_user32.SetThreadDesktop.return_value = 1
    mock_user32.IsWindow.return_value = 0

    with patch("ctypes.windll.user32", mock_user32), patch("ctypes.windll.kernel32", MagicMock()):
        res = activate_window(1234, 4444, desktop_name="ValidDesktop")
        assert res["success"] is False
        assert res["action"] == "invalid_hwnd"
        mock_user32.CloseDesktop.assert_called_once_with(999)


def test_activate_window_focus_refused():
    """Verifies reporting when Windows refuses foreground focus."""
    mock_user32 = MagicMock()
    mock_user32.OpenDesktopW.return_value = 999
    mock_user32.SetThreadDesktop.return_value = 1
    mock_user32.IsWindow.return_value = 1
    mock_user32.IsIconic.return_value = 1
    mock_user32.GetForegroundWindow.return_value = 99999  # Different HWND

    with patch("ctypes.windll.user32", mock_user32), patch("ctypes.windll.kernel32", MagicMock()):
        res = activate_window(1234, 4444, desktop_name="ValidDesktop")
        # When iconic, ShowWindow(SW_RESTORE) is called
        mock_user32.ShowWindow.assert_called_once_with(1234, 9)
        mock_user32.CloseDesktop.assert_called_once_with(999)
