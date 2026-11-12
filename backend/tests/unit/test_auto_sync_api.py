import pytest
from datetime import date, datetime, timezone
from unittest.mock import patch
from fastapi import HTTPException
from app.api.auto_sync import get_auto_sync_config, update_auto_sync_config, trigger_auto_sync_now, AutoSyncConfigUpdate
from app.services.scheduler.auto_sync_service import AutoSyncService, compute_sync_date_range
from app.core.auth import get_admin_config


def test_auto_sync_service_and_endpoints():
    import time
    from unittest.mock import patch
    token = "test_valid_admin_token_autosync"
    mock_cfg = dict(get_admin_config())
    mock_cfg["active_tokens"] = [{"token": token, "created_at": time.time()}]
    auth_header = f"Bearer {token}"

    svc = AutoSyncService.get_instance()
    svc.stop()

    # 1. get_auto_sync_config (public read-only)
    res = get_auto_sync_config()
    assert res["success"] is True
    assert "data" in res
    cfg = res["data"]
    assert "enabled" in cfg
    assert "interval_minutes" in cfg
    assert "sync_chains" in cfg
    assert "is_running" in cfg
    assert "sync_mode" in cfg

    # 2. update_auto_sync_config
    update_data = AutoSyncConfigUpdate(
        enabled=True,
        interval_minutes=30,
        sync_chains=["fpt_shop", "long_chau"],
        date_range_days=14,
        sync_mode="days"
    )

    # 2a. Verify that direct unauthenticated call is rejected with HTTP 401
    with pytest.raises(HTTPException) as exc_info:
        update_auto_sync_config(update_data)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Chưa có token xác thực!"

    # 2b. Authorized call succeeds with valid token
    with patch("app.core.auth.get_admin_config", return_value=mock_cfg):
        res_update = update_auto_sync_config(update_data, authorization=auth_header)
    assert res_update["success"] is True
    updated = res_update["data"]
    assert updated["enabled"] is True
    assert updated["interval_minutes"] == 30
    assert updated["sync_chains"] == ["fpt_shop", "long_chau"]
    assert updated["date_range_days"] == 14
    assert updated["sync_mode"] == "days"
    assert updated["next_run_at"] is not None

    # 2c. update_auto_sync_config with current_month and specific_month
    update_month = AutoSyncConfigUpdate(
        sync_mode="specific_month",
        specific_month="2026-09"
    )
    with patch("app.core.auth.get_admin_config", return_value=mock_cfg):
        res_month = update_auto_sync_config(update_month, authorization=auth_header)
    assert res_month["success"] is True
    assert res_month["data"]["sync_mode"] == "specific_month"
    assert res_month["data"]["specific_month"] == "2026-09"

    # Test compute_sync_date_range
    # Specific month (September has 30 days)
    s_date, e_date = compute_sync_date_range({"sync_mode": "specific_month", "specific_month": "2026-09"})
    assert s_date == date(2026, 9, 1)
    assert e_date == date(2026, 9, 30)

    # Specific month for February in non-leap year (2025 has 28 days)
    s_feb, e_feb = compute_sync_date_range({"sync_mode": "specific_month", "specific_month": "2025-02"})
    assert s_feb == date(2025, 2, 1)
    assert e_feb == date(2025, 2, 28)

    # Current month
    today = datetime.now(timezone.utc).date()
    s_cur, e_cur = compute_sync_date_range({"sync_mode": "current_month"})
    assert s_cur == today.replace(day=1)
    assert e_cur == today

    # 3. trigger_auto_sync_now
    # 3a. Direct unauthenticated call is rejected with HTTP 401
    with pytest.raises(HTTPException) as exc_info:
        trigger_auto_sync_now()
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Chưa có token xác thực!"

    # 3b. Authorized call succeeds
    with patch("app.core.auth.get_admin_config", return_value=mock_cfg):
        with patch.object(svc, "trigger_run_now", return_value={"success": True, "message": "Started"}):
            res_run = trigger_auto_sync_now(authorization=auth_header)
            assert res_run["success"] is True

    # 4. Restore clean disabled state with current_month mode
    restore_data = AutoSyncConfigUpdate(
        enabled=False,
        interval_minutes=60,
        sync_chains=["fpt_shop", "long_chau", "vaccine"],
        date_range_days=30,
        sync_mode="current_month",
        specific_month=None
    )
    with patch("app.core.auth.get_admin_config", return_value=mock_cfg):
        res_restore = update_auto_sync_config(restore_data, authorization=auth_header)
    assert res_restore["success"] is True
    assert res_restore["data"]["enabled"] is False
    assert res_restore["data"]["next_run_at"] is None
    assert res_restore["data"]["sync_mode"] == "current_month"
