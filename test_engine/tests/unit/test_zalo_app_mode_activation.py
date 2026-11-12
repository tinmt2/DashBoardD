"""
Comprehensive Unit Tests for Zalo App Mode and Window Activation (Phase 8.1F).
Verifies:
1. Chrome App Mode flag (--app=https://chat.zalo.me) when headless=False.
2. Re-use branch does NOT no-op but invokes activate_window.
3. Headless mode preservation.
4. Window activation response reporting.
5. Router integration with structured ApiResponse.
"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.zalo_web_adapter import ZaloWebAdapter
from app.api.routes.zalo_router import open_zalo_browser, OpenBrowserRequest


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
def adapter():
    a = ZaloWebAdapter()
    a.driver = None
    a._is_opening = False
    return a


def test_open_browser_app_mode_params(adapter):
    """Verifies that create_chrome_driver is called with app_url and start_maximized=False."""
    mock_driver = MagicMock()
    mock_driver.current_url = "https://chat.zalo.me/"
    mock_driver.window_handles = ["handle1"]

    with patch("app.services.zalo_web_adapter.create_chrome_driver", return_value=mock_driver) as mock_create:
        with patch.object(adapter, "activate_window", return_value={"success": True, "activated": True, "action": "foreground", "message": "OK"}):
            with patch("app.services.zalo_web_adapter.cleanup_chrome_sessions"):
                result = adapter.open_browser(headless=False)

                # Verify create_chrome_driver arguments
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs.get("app_url") == "https://chat.zalo.me"
                assert call_kwargs.get("start_maximized") is False
                assert call_kwargs.get("headless") is False

                assert result["success"] is True
                assert result["mode"] == "app"
                assert result["activated"] is True


def test_open_browser_headless_mode_params(adapter):
    """Verifies that headless mode does not pass app_url and sets headless=True."""
    mock_driver = MagicMock()
    mock_driver.current_url = "https://chat.zalo.me/"
    mock_driver.window_handles = ["handle1"]

    with patch("app.services.zalo_web_adapter.create_chrome_driver", return_value=mock_driver) as mock_create:
        with patch("app.services.zalo_web_adapter.cleanup_chrome_sessions"):
            result = adapter.open_browser(headless=True)

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs.get("app_url") is None
            assert call_kwargs.get("headless") is True

            assert result["success"] is True
            assert result["mode"] == "headless"


def test_open_browser_reuse_branch_activates_window(adapter):
    """Verifies that re-using an active GUI browser invokes activate_window and does not no-op."""
    mock_driver = MagicMock()
    mock_driver.current_url = "https://chat.zalo.me/"
    adapter.driver = mock_driver
    adapter.is_headless = False

    expected_act = {
        "success": True,
        "activated": True,
        "action": "foreground",
        "message": "Cửa sổ Zalo đã được đưa lên phía trước màn hình.",
        "hwnd": 12345
    }

    with patch.object(adapter, "activate_window", return_value=expected_act) as mock_act:
        result = adapter.open_browser(headless=False)

        # Must call activate_window
        mock_act.assert_called_once()
        assert result == expected_act
        # Driver must NOT be destroyed or re-created
        assert adapter.driver is mock_driver


def test_open_browser_reuse_branch_headless(adapter):
    """Verifies that re-using an active headless browser returns reused status cleanly."""
    mock_driver = MagicMock()
    mock_driver.current_url = "https://chat.zalo.me/"
    adapter.driver = mock_driver
    adapter.is_headless = True

    result = adapter.open_browser(headless=True)
    assert result["success"] is True
    assert result["action"] == "reused"
    assert "ngầm" in result["message"]


@pytest.mark.anyio
async def test_zalo_router_open_browser_endpoint():
    """Verifies that the FastAPI endpoint extracts structured dictionary and returns ApiResponse."""
    req = OpenBrowserRequest(headless=False)
    fake_res = {
        "success": True,
        "activated": True,
        "action": "foreground",
        "message": "Cửa sổ Zalo đã được đưa lên phía trước màn hình."
    }

    with patch("app.services.zalo_web_adapter.zalo_web_adapter.open_browser", return_value=fake_res):
        with patch("app.services.zalo_monitor_service.zalo_monitor_service.log_event"):
            api_res = await open_zalo_browser(req)
            assert api_res.success is True
            assert api_res.status == "ok"
            assert "đưa lên phía trước" in api_res.message
            assert api_res.data["action"] == "foreground"
