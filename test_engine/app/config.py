import json
import re
from copy import deepcopy
from functools import lru_cache
from typing import Any

from app.paths import BASE_DIR  # type: ignore

from app.paths import RUNTIME_DIR
CONFIG_FILE = RUNTIME_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "paths": {
        "region_file": "",
        "warehouse_file": "",
    },
    "gsheet": {
        "cred_file": "Checkcam.json",
        "spreadsheet_id": "1hK2NYEjELl-8qapOQ72nS3E2iKrOAz9BwsLACZDcEaQ",
        "target_gid": 1062029638,
        "sheet_cam_mkn": "Cam mkn",
        "sheet_summary": "Tổng camera",
    },
    "check_cam": {
        "known_errors_csv_url": "https://docs.google.com/spreadsheets/d/1hK2NYEjELl-8qapOQ72nS3E2iKrOAz9BwsLACZDcEaQ/export?format=csv&gid=0",
        "enable_playback_last_time": True,
        "playback_days": 7,
        "playback_use_local_time": True,
        "playback_end_margin_hours": 2,
        "playback_debug_ip": "",
        "playback_debug_max": 1,
        "periodic_enabled": False,
        "periodic_auto_sync": True,
        "periodic_interval_minutes": 15,
        "recovery_sheet_name": "Cam chập chờn",
    },
    "zalo_monitor": {
        "fixed_group_name": "GS AN NINH",
        "batch_interval_minutes": 5,
        "handover_max_lines": 6,
        "spreadsheet_id": "10U1IXvxvvFPsAktojDx9VgYbMdAYZ3y7-gABdWATcxQ",
        "sheet_zalo_monitor": "Gs An Ninh",
        "sheet_zalo_handover": "Zalo_Bao_Cao_Ca",
    },
}


def _deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def _parse_spreadsheet_id(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    # Accept full URL or raw key
    m = re.search(r"/d/([a-zA-Z0-9-_]+)", value)
    if m:
        return m.group(1)
    return value


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
    cfg = deepcopy(DEFAULT_CONFIG)

    # Merge new-structure keys first
    if isinstance(raw, dict):
        _deep_merge(cfg, raw)

    # Backward-compatible mapping from old flat keys
    if isinstance(raw, dict):
        if "region_file" in raw:
            cfg["paths"]["region_file"] = raw.get("region_file", "")
        if "warehouse_file" in raw:
            cfg["paths"]["warehouse_file"] = raw.get("warehouse_file", "")
        if "google_cred_file" in raw:
            cfg["gsheet"]["cred_file"] = raw.get("google_cred_file", cfg["gsheet"]["cred_file"])
        if "google_sheet_id" in raw:
            cfg["gsheet"]["spreadsheet_id"] = _parse_spreadsheet_id(raw.get("google_sheet_id", ""))
    # Drop legacy flat keys from normalized output
    for k in (
        "region_file",
        "warehouse_file",
        "google_cred_file",
        "google_sheet_id",
        "google_sheet_name",
    ):
        cfg.pop(k, None)

    cfg["gsheet"]["spreadsheet_id"] = _parse_spreadsheet_id(cfg["gsheet"].get("spreadsheet_id", ""))
    cfg["gsheet"]["target_gid"] = _coerce_int(cfg["gsheet"].get("target_gid"), DEFAULT_CONFIG["gsheet"]["target_gid"])
    cfg["gsheet"]["cred_file"] = cfg["gsheet"].get("cred_file") or DEFAULT_CONFIG["gsheet"]["cred_file"]

    return cfg


def load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
    else:
        raw = {}
    return normalize_config(raw)


def save_config(cfg: dict[str, Any]) -> None:
    normalized = normalize_config(cfg)
    CONFIG_FILE.write_text(json.dumps(normalized, ensure_ascii=False, indent=4), encoding="utf-8")


@lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:
    return load_config()


def reload_config() -> dict[str, Any]:
    get_config.cache_clear()
    return get_config()
