import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "runtime", "zalo_monitor.db")

def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS zalo_messages (
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
    # Bổ sung các cột mới nếu bảng đã tạo từ trước
    try:
        cursor.execute("ALTER TABLE zalo_messages ADD COLUMN thread_root_hash TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE zalo_messages ADD COLUMN quote_data_json TEXT")
    except Exception:
        pass

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_msg_hash ON zalo_messages(msg_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_status ON zalo_messages(ai_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_status ON zalo_messages(sheet_sync_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_thread_root ON zalo_messages(thread_root_hash)")
    conn.commit()
    conn.close()

def save_raw_message(
    msg_hash: str, 
    group_name: str, 
    sender: str, 
    raw_content: str, 
    sent_at: Optional[str] = None,
    thread_root_hash: Optional[str] = None,
    quote_json: Optional[str] = None
) -> bool:
    """Lưu toàn bộ tin nhắn nhận được. Mặc định đặt sheet_sync_status = 'PENDING' để sẵn sàng đồng bộ toàn bộ."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_sent = (sent_at or "").strip()

    try:
        cursor.execute("""
        INSERT INTO zalo_messages (
            msg_hash, group_name, sender, raw_content, detected_at, sent_at, 
            ai_status, sheet_sync_status, thread_root_hash, quote_data_json
        )
        VALUES (?, ?, ?, ?, ?, ?, 'PENDING', 'PENDING', ?, ?)
        """, (msg_hash, group_name, sender, raw_content, now_str, clean_sent, thread_root_hash, quote_json))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Nếu bản ghi đã có từ trước mà lúc trước bị lưu sai giờ quét (dài hơn 5 ký tự hoặc lệch giờ)
        # thì cập nhật lại giờ thực tế chính xác từ lần quét này
        if clean_sent and ":" in clean_sent:
            cursor.execute("SELECT id, sent_at, raw_content FROM zalo_messages WHERE msg_hash = ?", (msg_hash,))
            existing = cursor.fetchone()
            if existing:
                old_sent = (existing["sent_at"] or "").strip()
                if old_sent != clean_sent:
                    old_c = existing["raw_content"]
                    new_c = old_c
                    time_part = clean_sent.split(" ")[-1][:5] if " " in clean_sent else clean_sent
                    if old_c.startswith("[") and ":" in old_c[:10]:
                        import re
                        new_c = re.sub(r'^\[\d{1,2}:\d{2}\]', f'[{time_part}]', old_c)

                    cursor.execute("""
                    UPDATE zalo_messages
                    SET sent_at = ?,
                        raw_content = ?,
                        sheet_sync_status = 'PENDING'
                    WHERE id = ?
                    """, (clean_sent, new_c, existing["id"]))
                    conn.commit()
        return False
    finally:
        conn.close()

def save_reply_message(
    msg_hash: str, 
    group_name: str, 
    sender: str, 
    raw_content: str, 
    sent_at: Optional[str], 
    thread_root_hash: str, 
    quote_json: Optional[str] = None
) -> bool:
    """
    Lưu bản ghi tin nhắn con (reply) vào database để kiểm tra trùng lặp và truy vết,
    nhưng đặt sheet_sync_status = 'THREAD_MERGED' để không đẩy riêng lẻ lên Google Sheets.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_sent = (sent_at or "").strip()
    try:
        cursor.execute("""
        INSERT INTO zalo_messages (
            msg_hash, group_name, sender, raw_content, detected_at, sent_at, 
            ai_status, sheet_sync_status, thread_root_hash, quote_data_json
        )
        VALUES (?, ?, ?, ?, ?, ?, 'SKIPPED', 'THREAD_MERGED', ?, ?)
        """, (msg_hash, group_name, sender, raw_content, now_str, clean_sent, thread_root_hash, quote_json))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def find_matching_root_message(group_name: str, quote_text: str, quote_sender: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Tìm kiếm tin nhắn gốc (root message) trong cùng nhóm phù hợp với nội dung được quote.
    Hỗ trợ cả trường hợp Zalo cắt ngắn nội dung quote bằng dấu '...' hoặc reply nhiều tầng (quote lại một reply trước đó).
    """
    if not quote_text:
        return None
    q_clean = quote_text.rstrip('.').strip().lower()
    if quote_sender:
        s_clean = quote_sender.strip().lower()
        if q_clean.startswith(s_clean):
            q_clean = q_clean[len(s_clean):].strip()

    if len(q_clean) < 3:
        return None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM zalo_messages
    WHERE group_name = ? AND thread_root_hash IS NULL
    ORDER BY id DESC
    LIMIT 150
    """, (group_name,))
    rows = [dict(r) for r in cursor.fetchall()]

    # 1. Khớp chính xác hoặc chuỗi con đầy đủ
    for r in rows:
        raw_lower = r["raw_content"].lower()
        if q_clean in raw_lower or raw_lower in q_clean:
            conn.close()
            return r

    # 2. Khớp tiền tố (tối thiểu 12 ký tự đầu) đề phòng Zalo cắt đuôi dài
    if len(q_clean) >= 12:
        prefix = q_clean[:20]
        for r in rows:
            if prefix in r["raw_content"].lower():
                conn.close()
                return r

    # 3. Hỗ trợ chuỗi hội thoại nhiều tầng (Reply quote lại một Reply trước đó):
    try:
        cursor.execute("""
        SELECT thread_root_hash FROM zalo_messages
        WHERE group_name = ? AND thread_root_hash IS NOT NULL
        AND lower(raw_content) LIKE ?
        ORDER BY id DESC LIMIT 1
        """, (group_name, f"%{q_clean[:25]}%"))
        sub_row = cursor.fetchone()
        if sub_row and sub_row["thread_root_hash"]:
            cursor.execute("SELECT * FROM zalo_messages WHERE msg_hash = ?", (sub_row["thread_root_hash"],))
            parent = cursor.fetchone()
            conn.close()
            if parent:
                return dict(parent)
    except Exception:
        pass

    conn.close()
    return None

def append_reply_to_thread(root_id: int, reply_sender: str, reply_time: str, reply_text: str, reply_hash: str) -> bool:
    """
    Nối tin nhắn phản hồi vào chuỗi hội thoại (thread) của tin nhắn gốc.
    Tự động chuẩn hóa định dạng cây:
    [10:00] Nguyễn Văn A: Cửa hàng ABC camera 03 bị mất hình
    ↳ [10:05] Trần Văn B: Đang kiểm tra nguồn switch
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM zalo_messages WHERE id = ?", (root_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    root_content = row["raw_content"]
    time_display = reply_time or "Ca"
    if " " in time_display:
        time_display = time_display.split(" ")[-1][:5]
    reply_line = f"↳ [{time_display}] {reply_sender}: {reply_text}"

    # Tránh nối trùng lặp nếu nội dung phản hồi đã có trong chuỗi
    if reply_text in root_content and reply_sender in root_content:
        conn.close()
        return False

    # Nếu tin nhắn gốc chưa được bọc format cây [Thời gian] Tác giả: ...
    if not root_content.startswith("["):
        root_time = row["sent_at"] or "00:00"
        if " " in root_time:
            root_time = root_time.split(" ")[-1][:5]
        root_sender = row["sender"] or "Thành viên"
        new_content = f"[{root_time}] {root_sender}: {root_content}\n{reply_line}"
    else:
        new_content = f"{root_content}\n{reply_line}"

    # Đặt lại sheet_sync_status = 'PENDING' để hệ thống tự động cập nhật đè lên dòng trên Google Sheets
    cursor.execute("""
    UPDATE zalo_messages
    SET raw_content = ?,
        sheet_sync_status = 'PENDING',
        ai_status = 'PENDING'
    WHERE id = ?
    """, (new_content, root_id))
    conn.commit()
    conn.close()
    return True

def get_pending_ai_messages(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM zalo_messages
    WHERE ai_status = 'PENDING'
    ORDER BY id ASC
    LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_ai_result(msg_id: int, is_error: bool, ai_status: str, ai_result: Optional[Dict[str, Any]] = None, error_msg: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    ai_json = json.dumps(ai_result, ensure_ascii=False) if ai_result else None
    
    # Quan trọng: Giữ sheet_sync_status là 'PENDING' cho TOÀN BỘ tin nhắn
    cursor.execute("""
    UPDATE zalo_messages
    SET is_error_candidate = ?,
        ai_status = ?,
        ai_result_json = ?,
        sheet_sync_status = 'PENDING',
        error_message = ?
    WHERE id = ? AND sheet_sync_status != 'SYNCED'
    """, (1 if is_error else 0, ai_status, ai_json, error_msg, msg_id))
    conn.commit()
    conn.close()

def get_pending_sync_messages(limit: int = 500, sync_all: bool = True) -> List[Dict[str, Any]]:
    """Lấy danh sách tin nhắn cần đồng bộ. sync_all=True cho phép đồng bộ TOÀN BỘ tin nhắn."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if sync_all:
        cursor.execute("""
        SELECT * FROM zalo_messages
        WHERE sheet_sync_status IN ('PENDING', 'FAILED') AND thread_root_hash IS NULL
        ORDER BY id ASC
        LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
        SELECT * FROM zalo_messages
        WHERE sheet_sync_status IN ('PENDING', 'FAILED') AND is_error_candidate = 1 AND thread_root_hash IS NULL
        ORDER BY id ASC
        LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_messages_for_gsheet_reconcile(limit: int = 500) -> List[Dict[str, Any]]:
    """Lấy danh sách tin nhắn gần đây để đối soát và bổ sung nếu trên Google Sheets bị thiếu."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM zalo_messages
    WHERE thread_root_hash IS NULL
    ORDER BY id ASC
    LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def clear_all_messages():
    """Xóa toàn bộ các bản ghi tin nhắn và reset lại bộ đếm ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM zalo_messages")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='zalo_messages'")
    conn.commit()
    conn.close()

def mark_messages_synced(msg_ids: List[int], sync_status: str = "SYNCED", error_msg: Optional[str] = None):
    if not msg_ids:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    placeholders = ",".join("?" * len(msg_ids))
    cursor.execute(f"""
    UPDATE zalo_messages
    SET sheet_sync_status = ?,
        sheet_synced_at = ?,
        error_message = ?
    WHERE id IN ({placeholders})
    """, (sync_status, now_str if sync_status == "SYNCED" else None, error_msg, *msg_ids))
    conn.commit()
    conn.close()

def get_monitor_stats() -> Dict[str, int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM zalo_messages")
    total_detected = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM zalo_messages WHERE is_error_candidate = 1")
    total_errors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM zalo_messages WHERE sheet_sync_status = 'SYNCED'")
    total_synced = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM zalo_messages WHERE sheet_sync_status = 'FAILED' OR ai_status = 'FAILED'")
    total_failed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM zalo_messages WHERE sheet_sync_status = 'PENDING'")
    total_pending = cursor.fetchone()[0]

    conn.close()
    return {
        "total_detected": total_detected,
        "total_errors": total_errors,
        "total_synced": total_synced,
        "total_failed": total_failed,
        "total_pending": total_pending
    }

def get_recent_messages(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM zalo_messages
    WHERE thread_root_hash IS NULL
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_msg_hashes() -> set:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT msg_hash FROM zalo_messages")
        rows = cursor.fetchall()
        conn.close()
        return {r[0] for r in rows if r[0]}
    except Exception:
        return set()

init_db()
