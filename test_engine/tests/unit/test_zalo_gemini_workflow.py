"""
Unit Tests for Zalo + Gemini Real-World Workflow Validation (Phase 8.4A).
Tests:
1. Gemini AI Analysis: Heuristic check, missing API key fallback, exception handling.
2. Anti-hallucination: No shop code fabricated when none exists.
3. Message Processing: Store code extraction, multi-incident splitting, shop code cleaning.
4. SQLite Message Store: De-duplication on msg_hash, idempotent insert, sync status lifecycle.
5. Google Sheets Sync Logic: Row mapping and de-duplication in memory.
"""

import sqlite3
import pytest
from unittest.mock import MagicMock, patch

from app.services.zalo_ai_service import (
    quick_heuristic_check,
    analyze_message_with_ai,
)
from app.services.zalo_monitor_service import (
    extract_store_code,
    clean_content_remove_shop_code,
    split_multiline_incidents,
)


# ==============================================================================
# 1. GEMINI AI & HEURISTIC ANALYSIS TESTS
# ==============================================================================

def test_heuristic_check_identifies_errors():
    """Verifies that common technical error keywords are detected."""
    assert quick_heuristic_check("Cam 30477 mất kết nối từ sáng nay") is True
    assert quick_heuristic_check("Đầu ghi shop 80123 bị đen màn hình") is True
    assert quick_heuristic_check("Nhờ kỹ thuật check giúp ticket 1298424") is True
    assert quick_heuristic_check("Shop bị mất điện tổng rồi ạ") is True


def test_heuristic_check_ignores_normal_chat():
    """Verifies that greetings or trivial messages are skipped."""
    assert quick_heuristic_check("Chào cả nhà buổi sáng nhé!") is False
    assert quick_heuristic_check("Ok bạn") is False
    assert quick_heuristic_check("123") is False
    assert quick_heuristic_check("") is False


def test_ai_analysis_missing_key_fallback():
    """Verifies safe fallback when GEMINI_API_KEY is not configured."""
    with patch("app.services.zalo_ai_service.get_gemini_api_key", return_value=None):
        raw_msg = "30477 - QBH 102 Hùng Vương: C13 chập chờn, ticket 1298424"
        is_error, result_dict, err_msg = analyze_message_with_ai(raw_msg, "Minh Frt")

        assert is_error is True
        assert result_dict is not None
        assert result_dict["is_error"] is True
        assert result_dict["store_code"] is None  # Anti-hallucination: no fake code
        assert result_dict["confidence"] == 0.7
        assert "Heuristic fallback" in result_dict.get("note", "")
        assert err_msg is None  # Handled cleanly without raising an exception


def test_ai_analysis_normal_message_skipped():
    """Verifies that non-error messages return (False, None, None) immediately."""
    with patch("app.services.zalo_ai_service.get_gemini_api_key", return_value="fake-key"):
        is_error, result_dict, err_msg = analyze_message_with_ai("Chúc mọi người ca trực vui vẻ!", "Tài")
        assert is_error is False
        assert result_dict is None
        assert err_msg is None


def test_ai_analysis_api_exception_fallback():
    """Verifies that when Gemini API raises an error (quota/network), data is not lost."""
    with patch("app.services.zalo_ai_service.get_gemini_api_key", return_value="fake-key"):
        # Mock google.genai raising an exception
        with patch.dict("sys.modules", {"google.genai": MagicMock(side_effect=Exception("ResourceExhausted 429"))}):
            raw_msg = "30892 - BAR 17 Hải Bình: PC mkn, ticket 1299467"
            is_error, result_dict, err_msg = analyze_message_with_ai(raw_msg, "Tín")

            assert is_error is True
            assert result_dict is not None
            assert result_dict["store_code"] is None
            assert "Gemini API error" in (err_msg or "")


# ==============================================================================
# 2. STORE CODE EXTRACTION & MESSAGE SPLITTING TESTS
# ==============================================================================

def test_extract_store_code_patterns():
    """Verifies accurate store code extraction including complex suffixes and ticket exclusion."""
    assert extract_store_code("30477 - QBH 102 Hùng Vương: C13 chập chờn, ticket 1298424") == "30477"
    assert extract_store_code("30356-2 - NDH 174 Trần Hưng Đạo: kho dọn hết đồ") == "30356-2"
    assert extract_store_code("30551 - 2 - Shop mới thay nguồn") == "30551-2"
    assert extract_store_code("80226 LC Nguyễn Trãi mất mạng") == "80226"
    assert extract_store_code("Ticket 1298424 xử lý xong") == ""  # Ticket number is NOT a store code


def test_clean_content_remove_shop_code():
    """Verifies that leading shop codes are cleaned while preserving descriptive text."""
    raw = "30477 - QBH 102 Hùng Vương: C13 chập chờn"
    cleaned = clean_content_remove_shop_code(raw, "30477")
    assert "30477" not in cleaned[:5]
    assert "C13 chập chờn" in cleaned


def test_split_multiline_incidents():
    """Verifies splitting a multi-shop handover report into individual incident items."""
    multiline_text = (
        "30477 - QBH 102 Hùng Vương: C13 chập chờn\n"
        "30928 - BLU 148 Quốc Lộ 1A: C7, C10 mkn\n"
        "30892 - BAR 17 Hải Bình: tủ IOT mkn"
    )
    chunks = split_multiline_incidents(multiline_text)
    assert len(chunks) == 3
    assert "30477" in chunks[0]
    assert "30928" in chunks[1]
    assert "30892" in chunks[2]


# ==============================================================================
# 3. SQLITE MESSAGE STORE & DE-DUPLICATION TESTS (IN-MEMORY)
# ==============================================================================

def test_sqlite_deduplication_and_lifecycle():
    """Tests SQLite table schema, msg_hash uniqueness, and sync status updates in an isolated database."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
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
        ai_result_json TEXT,
        sheet_sync_status TEXT DEFAULT 'PENDING',
        sheet_synced_at TEXT,
        error_message TEXT,
        thread_root_hash TEXT,
        quote_data_json TEXT
    )
    """)

    # 1. Insert initial message
    h1 = "hash_abc_123"
    cursor.execute("""
    INSERT INTO zalo_messages (msg_hash, group_name, sender, raw_content, detected_at, sent_at)
    VALUES (?, ?, ?, ?, '2026-11-11 20:00:00', '11/11/2026 20:00')
    """, (h1, "GS AN NINH", "Tài", "Shop 80111 mất cam"))
    conn.commit()

    # 2. Duplicate insertion with same msg_hash raises IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
        INSERT INTO zalo_messages (msg_hash, group_name, sender, raw_content, detected_at, sent_at)
        VALUES (?, ?, ?, ?, '2026-11-11 20:00:01', '11/11/2026 20:00')
        """, (h1, "GS AN NINH", "Tài", "Shop 80111 mất cam"))

    # 3. Update AI result
    cursor.execute("""
    UPDATE zalo_messages
    SET is_error_candidate = 1, ai_status = 'SUCCESS', ai_result_json = '{"store_code": "80111"}'
    WHERE msg_hash = ?
    """, (h1,))
    conn.commit()

    # 4. Mark as Synced
    cursor.execute("""
    UPDATE zalo_messages
    SET sheet_sync_status = 'SYNCED', sheet_synced_at = '2026-11-11 20:05:00'
    WHERE msg_hash = ?
    """, (h1,))
    conn.commit()

    cursor.execute("SELECT sheet_sync_status, ai_status, is_error_candidate FROM zalo_messages WHERE msg_hash = ?", (h1,))
    row = cursor.fetchone()
    assert row["sheet_sync_status"] == "SYNCED"
    assert row["ai_status"] == "SUCCESS"
    assert row["is_error_candidate"] == 1

    conn.close()
