import os
import json
import logging
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationCreate, ChainSyncDetail
from app.services.fpt_shop.sync_db import sync_fpt_shop_data
from app.services.fpt_shop.browser_session import FPTBrowserSession
from app.services.long_chau.login.browser_session import LongChauBrowserSession
from app.services.long_chau.api.client import LongChauApiClient
from app.services.long_chau.api.sync_db import save_long_chau_api_records
from app.services.vaccine.login.browser_session import VaccineBrowserSession
from app.services.vaccine.api.sync_db import sync_vaccine_data

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".browser"))
CONFIG_FILE = os.path.join(CONFIG_DIR, "auto_sync_config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "interval_minutes": 60,
    "sync_chains": ["fpt_shop", "long_chau", "vaccine"],
    "date_range_days": 30,
    "last_run_at": None,
    "next_run_at": None,
    "last_status": None,
    "last_message": None,
}


class AutoSyncService:
    _instance: Optional["AutoSyncService"] = None
    _lock = threading.RLock()

    def __init__(self):
        self.config: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self.is_running: bool = False
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._load_config()

    @classmethod
    def get_instance(cls) -> "AutoSyncService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _load_config(self) -> None:
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR, exist_ok=True)
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.config.update(data)
                        logger.info(f"[AUTO_SYNC] Loaded config: enabled={self.config.get('enabled')}, interval={self.config.get('interval_minutes')}m")

            # Validate next_run_at
            now_utc = datetime.now(timezone.utc)
            if self.config.get("enabled"):
                next_str = self.config.get("next_run_at")
                interval = int(self.config.get("interval_minutes", 60))
                if not next_str:
                    self.config["next_run_at"] = (now_utc + timedelta(minutes=interval)).isoformat()
                else:
                    try:
                        clean_str = next_str.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(clean_str)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        if dt <= now_utc:
                            self.config["next_run_at"] = (now_utc + timedelta(minutes=interval)).isoformat()
                    except Exception:
                        self.config["next_run_at"] = (now_utc + timedelta(minutes=interval)).isoformat()
            else:
                self.config["next_run_at"] = None

            self._save_config()
        except Exception as e:
            logger.warning(f"[AUTO_SYNC] Could not load config: {e}")

    def _save_config(self) -> None:
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[AUTO_SYNC] Failed to save config: {e}")

    def get_status_info(self) -> Dict[str, Any]:
        with self._lock:
            return {
                **self.config,
                "is_running": self.is_running,
            }

    def update_config(self, new_cfg: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            now_utc = datetime.now(timezone.utc)
            if "interval_minutes" in new_cfg:
                val = int(new_cfg["interval_minutes"])
                if val < 5:
                    val = 5
                self.config["interval_minutes"] = val

            if "enabled" in new_cfg:
                now_enabled = bool(new_cfg["enabled"])
                self.config["enabled"] = now_enabled
                if now_enabled:
                    interval = int(self.config.get("interval_minutes", 60))
                    self.config["next_run_at"] = (now_utc + timedelta(minutes=interval)).isoformat()
                else:
                    self.config["next_run_at"] = None
            elif self.config.get("enabled") and "interval_minutes" in new_cfg:
                interval = int(self.config.get("interval_minutes", 60))
                self.config["next_run_at"] = (now_utc + timedelta(minutes=interval)).isoformat()

            if "sync_chains" in new_cfg and isinstance(new_cfg["sync_chains"], list):
                self.config["sync_chains"] = [str(c) for c in new_cfg["sync_chains"]]

            if "date_range_days" in new_cfg:
                days = int(new_cfg["date_range_days"])
                self.config["date_range_days"] = max(1, min(days, 365))

            self._save_config()
            logger.info(f"[AUTO_SYNC] Updated config: {self.config}")
            return self.get_status_info()

    def start(self) -> None:
        with self._lock:
            if self._worker_thread and self._worker_thread.is_alive():
                return
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True, name="AutoSyncWorker")
            self._worker_thread.start()
            logger.info("[AUTO_SYNC] Background worker thread started.")

    def stop(self) -> None:
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=0.5)
            logger.info("[AUTO_SYNC] Background worker thread stopped.")

    def trigger_run_now(self) -> Dict[str, Any]:
        with self._lock:
            if self.is_running:
                return {"success": False, "message": "Tiến trình đồng bộ đang chạy, vui lòng chờ."}

        t = threading.Thread(target=self._run_sync_job, args=("MANUAL",), daemon=True)
        t.start()
        return {"success": True, "message": "Đã bắt đầu tiến trình đồng bộ ngầm ngay bây giờ."}

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self.config.get("enabled"):
                    next_str = self.config.get("next_run_at")
                    interval = int(self.config.get("interval_minutes", 60))
                    now_utc = datetime.now(timezone.utc)

                    if not next_str:
                        next_dt = now_utc + timedelta(minutes=interval)
                        with self._lock:
                            self.config["next_run_at"] = next_dt.isoformat()
                            self._save_config()
                    else:
                        try:
                            clean_str = next_str.replace("Z", "+00:00")
                            next_dt = datetime.fromisoformat(clean_str)
                            if next_dt.tzinfo is None:
                                next_dt = next_dt.replace(tzinfo=timezone.utc)

                            if now_utc >= next_dt and not self.is_running:
                                logger.info(f"[AUTO_SYNC] Due time reached ({next_str}), executing scheduled sync...")
                                self._run_sync_job(trigger_mode="SCHEDULED")
                        except Exception as parse_err:
                            logger.error(f"[AUTO_SYNC] Error parsing next_run_at '{next_str}': {parse_err}")
                            with self._lock:
                                self.config["next_run_at"] = (now_utc + timedelta(minutes=interval)).isoformat()
                                self._save_config()
            except Exception as e:
                logger.error(f"[AUTO_SYNC] Error in worker loop: {e}")

            # Sleep in short slices
            for _ in range(5):
                if self._stop_event.is_set():
                    break
                time.sleep(1.0)

    def _run_sync_job(self, trigger_mode: str = "SCHEDULED") -> None:
        if self.is_running:
            logger.warning("[AUTO_SYNC] Sync already in progress, skipping duplicate trigger.")
            return

        with self._lock:
            self.is_running = True

        logger.info(f"[AUTO_SYNC] Starting sync execution (trigger={trigger_mode})...")
        db = SessionLocal()
        try:
            days = self.config.get("date_range_days", 30)
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=days)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            chains = self.config.get("sync_chains", ["fpt_shop", "long_chau", "vaccine"])
            chain_details: List[ChainSyncDetail] = []

            # 1. FPT Shop
            if "fpt_shop" in chains:
                logger.info(f"[AUTO_SYNC] Syncing FPT Shop from {start_str} to {end_str}...")
                try:
                    fpt_res = sync_fpt_shop_data(db, start_date, end_date)
                    if fpt_res.get("success"):
                        chain_details.append(ChainSyncDetail(
                            chain="FPT Shop",
                            status="SUCCESS",
                            new_records=fpt_res.get("new_records", 0),
                            total_rows=fpt_res.get("total_rows", 0),
                            duplicate_records=fpt_res.get("duplicate_records", 0),
                            error_message=None
                        ))
                    else:
                        chain_details.append(ChainSyncDetail(
                            chain="FPT Shop",
                            status="FAILED",
                            new_records=0,
                            total_rows=0,
                            duplicate_records=0,
                            error_message=fpt_res.get("error_message") or "Lỗi tải báo cáo FPT Shop"
                        ))
                except Exception as e:
                    logger.error(f"[AUTO_SYNC] FPT Shop sync exception: {e}")
                    chain_details.append(ChainSyncDetail(
                        chain="FPT Shop",
                        status="FAILED",
                        new_records=0,
                        total_rows=0,
                        duplicate_records=0,
                        error_message=str(e)
                    ))

            # 2. Long Châu
            if "long_chau" in chains:
                logger.info(f"[AUTO_SYNC] Syncing Long Châu from {start_str} to {end_str}...")
                try:
                    lc_session = LongChauBrowserSession.get_instance()
                    lc_status = lc_session.get_status()
                    has_cached = bool(getattr(lc_session, "cached_cookies", None) and any(k in lc_session.cached_cookies for k in ['budibase:auth', 'bb-auth']))
                    if not has_cached and (lc_status == "STOPPED" or lc_session.driver is None):
                        lc_status = lc_session.start(probe_only=True)

                    if lc_status != "AUTHENTICATED":
                        chain_details.append(ChainSyncDetail(
                            chain="Long Châu",
                            status="FAILED",
                            new_records=0,
                            total_rows=0,
                            duplicate_records=0,
                            error_message="Chưa đăng nhập Long Châu hoặc phiên đã hết hạn"
                        ))
                    else:
                        cookies = lc_session.get_auth_cookies()
                        headers = lc_session.get_auth_headers() if hasattr(lc_session, 'get_auth_headers') else None
                        client = LongChauApiClient(cookies, headers)
                        records = client.get_full_report(start_str, end_str)
                        inserted, duplicates = save_long_chau_api_records(db, records)
                        chain_details.append(ChainSyncDetail(
                            chain="Long Châu",
                            status="SUCCESS",
                            new_records=inserted,
                            total_rows=len(records),
                            duplicate_records=duplicates,
                            error_message=None
                        ))
                except Exception as e:
                    logger.error(f"[AUTO_SYNC] Long Châu sync exception: {e}")
                    chain_details.append(ChainSyncDetail(
                        chain="Long Châu",
                        status="FAILED",
                        new_records=0,
                        total_rows=0,
                        duplicate_records=0,
                        error_message=str(e)
                    ))

            # 3. Vaccine
            if "vaccine" in chains:
                logger.info(f"[AUTO_SYNC] Syncing Vaccine from {start_str} to {end_str}...")
                try:
                    vac_session = VaccineBrowserSession.get_instance()
                    vac_status = vac_session.get_status()
                    has_cached = bool(getattr(vac_session, "cached_cookies", None) and any(k in vac_session.cached_cookies for k in ['budibase:auth', 'bb-auth']))
                    if not has_cached and (vac_status == "STOPPED" or vac_session.driver is None):
                        vac_status = vac_session.start(probe_only=True)

                    if vac_status != "AUTHENTICATED":
                        chain_details.append(ChainSyncDetail(
                            chain="Vaccine",
                            status="FAILED",
                            new_records=0,
                            total_rows=0,
                            duplicate_records=0,
                            error_message="Chưa đăng nhập Vaccine hoặc phiên đã hết hạn"
                        ))
                    else:
                        cookies = vac_session.get_auth_cookies()
                        headers = vac_session.get_auth_headers()
                        res = sync_vaccine_data(db, cookies, headers, start_str, end_str)
                        if res.get("success"):
                            chain_details.append(ChainSyncDetail(
                                chain="Vaccine",
                                status="SUCCESS",
                                new_records=res.get("inserted", 0),
                                total_rows=res.get("total", res.get("inserted", 0) + res.get("duplicates", 0)),
                                duplicate_records=res.get("duplicates", 0),
                                error_message=None
                            ))
                        else:
                            chain_details.append(ChainSyncDetail(
                                chain="Vaccine",
                                status="FAILED",
                                new_records=0,
                                total_rows=0,
                                duplicate_records=0,
                                error_message=res.get("message") or "Đồng bộ dữ liệu Vaccine thất bại"
                            ))
                except Exception as e:
                    logger.error(f"[AUTO_SYNC] Vaccine sync exception: {e}")
                    chain_details.append(ChainSyncDetail(
                        chain="Vaccine",
                        status="FAILED",
                        new_records=0,
                        total_rows=0,
                        duplicate_records=0,
                        error_message=str(e)
                    ))

            # Summary calculation
            successes = [c for c in chain_details if c.status == "SUCCESS"]
            failures = [c for c in chain_details if c.status == "FAILED"]
            total_new = sum(c.new_records for c in chain_details)
            total_scanned = sum(c.total_rows for c in chain_details)
            total_dupes = sum(c.duplicate_records for c in chain_details)

            if len(failures) == 0 and len(successes) > 0:
                overall_status = "SUCCESS"
                if total_new > 0:
                    title = f"Tự động đồng bộ hoàn tất (+{total_new} lỗi/calllog mới)"
                else:
                    title = "Tự động đồng bộ máy chủ hoàn tất"
            elif len(successes) > 0:
                overall_status = "PARTIAL"
                if total_new > 0:
                    title = f"Tự động đồng bộ một phần (+{total_new} lỗi mới)"
                else:
                    title = "Tự động đồng bộ hoàn tất một phần"
            else:
                overall_status = "FAILED"
                title = "Tự động đồng bộ máy chủ thất bại"

            error_summary = None
            if failures:
                error_summary = "; ".join(f"{c.chain}: {c.error_message}" for c in failures)

            summary_msg = f"Đã quét {total_scanned} bản ghi, thêm mới {total_new} lỗi/calllog ({len(successes)}/{len(chain_details)} chuỗi thành công)."

            # Record notification in database
            repo = NotificationRepository(db)
            notif_data = NotificationCreate(
                title=title,
                status=overall_status,
                sync_type="AUTO_SYNC",
                start_date=start_str,
                end_date=end_str,
                total_new_errors=total_new,
                total_scanned=total_scanned,
                total_duplicates=total_dupes,
                chain_details=chain_details,
                error_message=error_summary,
            )
            repo.create(notif_data)
            logger.info(f"[AUTO_SYNC] Job completed: {overall_status}. {summary_msg}")

            # Update auto sync config status
            now_utc = datetime.now(timezone.utc)
            with self._lock:
                self.config["last_run_at"] = now_utc.isoformat()
                self.config["last_status"] = overall_status
                self.config["last_message"] = summary_msg
                if self.config.get("enabled"):
                    interval = int(self.config.get("interval_minutes", 60))
                    self.config["next_run_at"] = (now_utc + timedelta(minutes=interval)).isoformat()
                self._save_config()

        except Exception as ex:
            logger.error(f"[AUTO_SYNC] Critical error in _run_sync_job: {ex}", exc_info=True)
            with self._lock:
                self.config["last_status"] = "FAILED"
                self.config["last_message"] = f"Lỗi hệ thống: {ex}"
                self._save_config()
        finally:
            db.close()
            with self._lock:
                self.is_running = False
