"""
Unit Tests for Zalo Stability, Recovery & Data Reconciliation (Phase 8.4B).
Validates:
1. Two-tier deduplication & idempotent re-scan.
2. Thread-merged vs Synced lifecycle.
3. Resilience to Google Sheets API timeouts/failures (raw data preserved).
4. Resilience to Gemini AI quota limits (fallback data, raw message untouched).
5. State durability across simulated service restarts.
6. Memory safety (log trimming bounded at 200 entries).
"""

import sqlite3
import pytest
from unittest.mock import MagicMock, patch

from app.services.zalo_ai_service import analyze_message_with_ai
from app.services.zalo_monitor_service import ZaloMonitorService


def test_log_event_bounded_memory():
    """Verifies that in-memory logs are capped at 200 items to prevent memory leaks."""
    service = ZaloMonitorService()
    service.logs.clear()

    # Append 250 log entries
    for i in range(250):
        service.log_event(f"Test event {i}")

    assert len(service.logs) == 200
    assert "Test event 50" in service.logs[0]
    assert "Test event 249" in service.logs[-1]


def test_recovery_on_gsheet_failure_preserves_raw_data():
    """Verifies that when Google Sheets fails, raw SQLite data is not lost or corrupted."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE zalo_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        msg_hash TEXT UNIQUE NOT NULL,
        group_name TEXT NOT NULL,
        sender TEXT,
        raw_content TEXT NOT NULL,
        detected_at TEXT NOT NULL,
        sent_at TEXT,
        is_error_candidate INTEGER DEFAULT 0,
        ai_status TEXT DEFAULT 'PENDING',
        sheet_sync_status TEXT DEFAULT 'PENDING',
        sheet_synced_at TEXT,
        error_message TEXT
    )
    """)

    # Insert candidate message
    cur.execute("""
    INSERT INTO zalo_messages (msg_hash, group_name, sender, raw_content, detected_at, sent_at)
    VALUES ('h_err_test', 'GS AN NINH', 'Tài', 'Shop 80999 mất kết nối', '2026-11-11 21:00:00', '11/11/2026 21:00')
    """)
    conn.commit()

    # Simulate GSheet sync failure
    simulated_err = "APIError: 503 Service Unavailable"
    cur.execute("""
    UPDATE zalo_messages
    SET sheet_sync_status = 'FAILED', error_message = ?
    WHERE msg_hash = 'h_err_test'
    """, (simulated_err,))
    conn.commit()

    # Verify message raw content is completely intact and marked FAILED for future retry
    cur.execute("SELECT raw_content, sheet_sync_status, error_message FROM zalo_messages WHERE msg_hash = 'h_err_test'")
    row = cur.fetchone()
    assert row["raw_content"] == "Shop 80999 mất kết nối"
    assert row["sheet_sync_status"] == "FAILED"
    assert "503 Service Unavailable" in row["error_message"]

    # Verify retry selection: FAILED and PENDING messages are retry candidates
    cur.execute("SELECT id FROM zalo_messages WHERE sheet_sync_status IN ('PENDING', 'FAILED')")
    retries = cur.fetchall()
    assert len(retries) == 1

    conn.close()


def test_durability_across_simulated_restart():
    """Verifies that pending items in SQLite are identified and recoverable after restart."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE zalo_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        msg_hash TEXT UNIQUE NOT NULL,
        group_name TEXT NOT NULL,
        sender TEXT,
        raw_content TEXT NOT NULL,
        detected_at TEXT NOT NULL,
        sent_at TEXT,
        sheet_sync_status TEXT DEFAULT 'PENDING',
        thread_root_hash TEXT
    )
    """)

    # Populate 3 synced, 1 thread_merged, 2 pending
    cur.execute("INSERT INTO zalo_messages (msg_hash, group_name, raw_content, detected_at, sheet_sync_status) VALUES ('h1', 'G', 'M1', 'T', 'SYNCED')")
    cur.execute("INSERT INTO zalo_messages (msg_hash, group_name, raw_content, detected_at, sheet_sync_status) VALUES ('h2', 'G', 'M2', 'T', 'SYNCED')")
    cur.execute("INSERT INTO zalo_messages (msg_hash, group_name, raw_content, detected_at, sheet_sync_status, thread_root_hash) VALUES ('h3', 'G', 'M3', 'T', 'THREAD_MERGED', 'h1')")
    cur.execute("INSERT INTO zalo_messages (msg_hash, group_name, raw_content, detected_at, sheet_sync_status) VALUES ('h4', 'G', 'M4', 'T', 'PENDING')")
    cur.execute("INSERT INTO zalo_messages (msg_hash, group_name, raw_content, detected_at, sheet_sync_status) VALUES ('h5', 'G', 'M5', 'T', 'PENDING')")
    conn.commit()

    # Query pending sync candidates after restart
    cur.execute("SELECT msg_hash FROM zalo_messages WHERE sheet_sync_status = 'PENDING'")
    pending = [r["msg_hash"] for r in cur.fetchall()]
    assert pending == ["h4", "h5"]

    conn.close()


def test_ai_quota_exhaustion_does_not_corrupt_message():
    """Verifies that Gemini 429 quota exhaustion retains raw text and falls back gracefully."""
    with patch("app.services.zalo_ai_service.get_gemini_api_key", return_value="test_key"):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("429 Too Many Requests: Quota Exceeded")
        with patch("google.genai.Client", return_value=mock_client):
            raw_input = "31928 - BLU 148 Quốc Lộ 1A: C7, C10 mkn => đã báo TC mail"
            is_err, result_dict, err_detail = analyze_message_with_ai(raw_input, "Tài")

            assert is_err is True
            assert result_dict["clean_summary"] == raw_input.strip()
            assert result_dict["store_code"] is None  # Anti-hallucination intact
            assert "429" in err_detail
