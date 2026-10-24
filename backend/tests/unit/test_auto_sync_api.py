import pytest
from unittest.mock import patch
from app.api.auto_sync import get_auto_sync_config, update_auto_sync_config, trigger_auto_sync_now, AutoSyncConfigUpdate
from app.services.scheduler.auto_sync_service import AutoSyncService


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

    # 2. update_auto_sync_config
    update_data = AutoSyncConfigUpdate(
        enabled=True,
        interval_minutes=30,
        sync_chains=["fpt_shop", "long_chau"],
        date_range_days=14
    )
    res_update = update_auto_sync_config(update_data)
    assert res_update["success"] is True
    updated = res_update["data"]
    assert updated["enabled"] is True
    assert updated["interval_minutes"] == 30
    assert updated["sync_chains"] == ["fpt_shop", "long_chau"]
    assert updated["date_range_days"] == 14
    assert updated["next_run_at"] is not None

    # 3. trigger_auto_sync_now
    with patch.object(svc, "trigger_run_now", return_value={"success": True, "message": "Started"}):
        res_run = trigger_auto_sync_now()
        assert res_run["success"] is True

    # 4. Restore clean disabled state
    restore_data = AutoSyncConfigUpdate(
        enabled=False,
        interval_minutes=60,
        sync_chains=["fpt_shop", "long_chau", "vaccine"],
        date_range_days=30
    )
    res_restore = update_auto_sync_config(restore_data)
    assert res_restore["success"] is True
    assert res_restore["data"]["enabled"] is False
    assert res_restore["data"]["next_run_at"] is None
