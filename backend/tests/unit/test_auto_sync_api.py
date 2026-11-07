import pytest
from datetime import date, datetime, timezone
from unittest.mock import patch
from app.api.auto_sync import get_auto_sync_config, update_auto_sync_config, trigger_auto_sync_now, AutoSyncConfigUpdate
from app.services.scheduler.auto_sync_service import AutoSyncService, compute_sync_date_range


def test_auto_sync_service_and_endpoints():
    svc = AutoSyncService.get_instance()
    svc.stop()

    # 1. get_auto_sync_config
    res = get_auto_sync_config()
    assert res["success"] is True
    assert "data" in res
    cfg = res["data"]
    assert "enabled" in cfg
    assert "interval_minutes" in cfg
    assert "sync_chains" in cfg
    assert "is_running" in cfg
    assert "sync_mode" in cfg

    # 2. update_auto_sync_config with custom days
    update_data = AutoSyncConfigUpdate(
        enabled=True,
        interval_minutes=30,
        sync_chains=["fpt_shop", "long_chau"],
        date_range_days=14,
        sync_mode="days"
    )
    res_update = update_auto_sync_config(update_data)
    assert res_update["success"] is True
    updated = res_update["data"]
    assert updated["enabled"] is True
    assert updated["interval_minutes"] == 30
    assert updated["sync_chains"] == ["fpt_shop", "long_chau"]
    assert updated["date_range_days"] == 14
    assert updated["sync_mode"] == "days"
    assert updated["next_run_at"] is not None

    # 2b. update_auto_sync_config with current_month and specific_month
    update_month = AutoSyncConfigUpdate(
        sync_mode="specific_month",
        specific_month="2026-09"
    )
    res_month = update_auto_sync_config(update_month)
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
    with patch.object(svc, "trigger_run_now", return_value={"success": True, "message": "Started"}):
        res_run = trigger_auto_sync_now()
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
    res_restore = update_auto_sync_config(restore_data)
    assert res_restore["success"] is True
    assert res_restore["data"]["enabled"] is False
    assert res_restore["data"]["next_run_at"] is None
    assert res_restore["data"]["sync_mode"] == "current_month"
