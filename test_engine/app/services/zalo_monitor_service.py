import os

import sys

import json

import time

import asyncio

import logging

from typing import Dict, Any, List, Optional

from datetime import datetime

import re

import pandas as pd



from app.services.zalo_db import (

    save_raw_message,

    save_reply_message,

    find_matching_root_message,

    append_reply_to_thread,

    get_pending_ai_messages,

    update_ai_result,

    get_pending_sync_messages,

    get_messages_for_gsheet_reconcile,

    clear_all_messages,

    mark_messages_synced,

    get_monitor_stats,

    get_recent_messages

)

from app.services.zalo_ai_service import analyze_message_with_ai

from app.services.zalo_web_adapter import zalo_web_adapter

from app.services.gsheet_sync import get_client, _resolve_cred_file

from app.config import get_config



logger = logging.getLogger(__name__)



def extract_store_code(text: str) -> str:
    """Trích xuất mã cửa hàng (hỗ trợ cả mã có hậu tố phụ như 30551-2, 30551 - 2, 58056_1, 82411) từ nội dung tin nhắn."""
    if not text:
        return ""
    cleaned = re.sub(r'(?i)ticket\s*\d+', '', text)
    # Hỗ trợ cả mã shop có hậu tố phụ dạng -2, -1, _2 kể cả có khoảng trắng (ví dụ: 30551-2, 30551 - 2)
    # Không lấy các hậu tố chữ như -LC, -BDG, -TBH vì đó là tên tỉnh/chuỗi đi kèm tên shop
    m = re.search(r'(?:^|[\s\[\]|:\/])(\b(?:3|5|8)\d{4}(?:\s*[-_]\s*\d+)?\b)', cleaned, re.MULTILINE)
    if m:
        return re.sub(r'\s+', '', m.group(1))
    m2 = re.search(r'(?:^|[\s\[\]|:\/])(\b[1-9]\d{3,4}(?:\s*[-_]\s*\d+)?\b)', cleaned, re.MULTILINE)
    if m2:
        return re.sub(r'\s+', '', m2.group(1))
    return ""


def clean_content_remove_shop_code(text: str, shop_code: str) -> str:
    """Loại bỏ mã shop và tiền tố thừa ở đầu nội dung tin nhắn vì đã có cột Mã shop riêng."""
    if not text:
        return ""
    res = text.strip()
    if shop_code:
        parts = re.split(r'[-_]', shop_code)
        code_pat = r'\s*[-_]\s*'.join(re.escape(p) for p in parts) if len(parts) > 1 else re.escape(shop_code)
        base_code = parts[0].strip()
        
        # 1. Xóa toàn bộ mã shop (kể cả hậu tố -2, khoảng trắng, xuống dòng) ở đầu
        res = re.sub(r'(?mi)^\s*(?:mã\s*shop|ma\s*shop)?\s*[:|-]*\s*' + code_pat + r'[\s\-—–|:]*', '', res)
        # 2. Xóa base_code ở đầu nếu dính kèm chữ tỉnh/chuỗi (ví dụ: 31482-BDG -> giữ BDG)
        if base_code != shop_code or '-' in text[:15]:
            res = re.sub(r'(?mi)^\s*' + re.escape(base_code) + r'[\s\-—–|:]*', '', res)
        # 3. Xử lý sau tiền tố [HH:MM] Tên:
        res = re.sub(r"(^\[\d{2}:\d{2}\][^:]*:\s*)" + code_pat + r"[\s\-|:]*", r"\g<1>", res)
        res = re.sub(r"(^\[\d{2}:\d{2}\][^:]*:\s*)" + re.escape(base_code) + r"[\s\-|:]*", r"\g<1>", res)
        
    # 4. Loại bỏ tiền tố "Tên Shop:" / "Ten Shop:" thừa ở đầu nội dung
    res = re.sub(r'(?mi)^\s*(?:tên\s*shop|ten\s*shop)\s*[:|-]*\s*', '', res)
    return res.strip()


def split_multiline_incidents(raw_text: str) -> List[str]:
    """
    Tách tin nhắn thông minh thành các hàng riêng biệt:
    1. Nếu tin nhắn chứa nhiều dòng sự vụ độc lập (mỗi dòng 1 mã shop khác nhau).
    2. Nếu tin nhắn Quote lại một tin khác nhưng nội dung trả lời để xử lý một mã shop mới khác,
       sẽ tự động tách shop mới thành hàng độc lập thay vì bị gộp vào luồng shop cũ.
    """
    if not raw_text:
        return []
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    if len(lines) <= 1:
        return [raw_text.strip()]
    
    chunks = []
    current_chunk = []
    current_chunk_shop = None
    
    for line in lines:
        code = extract_store_code(line)
        if code:
            if current_chunk_shop is None:
                current_chunk.append(line)
                current_chunk_shop = code
            elif code != current_chunk_shop:
                # Phát hiện mã shop mới khác với shop đang xử lý ở trên
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                # Bỏ ký hiệu mũi tên phản hồi (↳) nếu có để biến thành hàng sự vụ độc lập
                clean_l = line
                if clean_l.startswith('↳') or clean_l.startswith('?'):
                    clean_l = clean_l[1:].strip()
                current_chunk = [clean_l]
                current_chunk_shop = code
            else:
                current_chunk.append(line)
        else:
            # Dòng phản hồi hoặc cập nhật không có mã shop mới -> gom vào sự vụ đang xử lý
            current_chunk.append(line)
            
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
        
    return chunks if chunks else [raw_text.strip()]


def detect_incident_status(text: str) -> str:
    """
    Phân tích thông minh trạng thái sự cố từ nội dung tin nhắn:
    - Mất nguồn tổng
    - Mất điện
    - Mất mạng
    - Logtag báo chậm
    - Lỗi camera
    - Online lại
    - Bình thường / Khác
    """
    if not text:
        return ""
    lower = text.lower()
    
    # 1. Mất nguồn tổng (ưu tiên cao nhất nếu nhắc đến nguồn tổng)
    if any(k in lower for k in ["mất nguồn tổng", "mat nguon tong", "mất nguồn", "mat nguon"]):
        return "Mất nguồn tổng"
        
    # 2. Mất điện (bao gồm cúp điện, mất cp, tắt nhầm cp)
    if any(k in lower for k in ["mất điện", "mat dien", "cúp điện", "cup dien", "mất cp", "mat cp", "tắt nhầm cp", "tat nham cp"]):
        return "Mất điện"
        
    # 3. Mất mạng (chỉ nhận diện khi có từ khóa rõ ràng như mất mạng, rớt mạng; các tin ghi 'mkn' chung chung thì để trống)
    if any(k in lower for k in ["mất mạng", "mat mang", "rớt mạng", "rot mang"]):
        return "Mất mạng"
        
    # 4. Logtag báo chậm
    if any(k in lower for k in ["logtag", "báo chậm", "bao cham"]):
        return "Logtag báo chậm"
        
    # 5. Lỗi camera / Mất hình / Hư hồng ngoại
    if any(k in lower for k in ["hư hồng ngoại", "hu hong ngoai", "mất hình", "mat hinh", "k hình", "k hinh", "hư cam", "hỏng cam", "bảo hành sống"]):
        return "Lỗi camera"
        
    # 6. Online lại
    if any(k in lower for k in ["shop onl", "đã onl", "da onl", "online lại"]):
        return "Online lại"
        
    return ""


def is_shift_handover_report(text: str, max_lines: int = 6) -> bool:

    """

    Nhận diện tin nhắn báo cáo giao ca / tổng kết cuối ca nhiều dòng.

    Các tin này được chuyển sang Tab phụ riêng 'Zalo_Bao_Cao_Ca' để không làm giãn chiều cao hàng trên Sheet chính.

    """

    if not text:

        return False

    clean_lines = [l.strip() for l in text.strip().split('\n') if l.strip()]

    if len(clean_lines) >= max_lines:

        return True

    lower_text = text.lower()

    handover_keywords = [

        "báo cáo ca", "bao cao ca", "giao ca", "bàn giao ca", "ban giao ca",

        "tổng kết ca", "tong ket ca", "ca sau theo dõi", "các ca sau", "ca sau nhắc"

    ]

    if any(kw in lower_text for kw in handover_keywords):

        return True

    if re.search(r'[-=]{3,}.*[-=]{3,}', text) or re.search(r'[-=]{4,}', text):

        if len(clean_lines) >= 3:

            return True

    shop_codes = re.findall(r'\b(?:3[0-9]{4}|8[0-9]{4})\b', text)

    if len(set(shop_codes)) >= 3:

        return True

    return False



class ZaloMonitorService:

    def __init__(self):

        self.is_running = False

        try:
            cfg = get_config()
            self.batch_interval_minutes = int(cfg.get('zalo_monitor', {}).get('batch_interval_minutes', 10))
        except Exception:
            self.batch_interval_minutes = 10

        self.last_batch_sync_time = time.time()

        self.task_handle: Optional[asyncio.Task] = None

        self.logs: List[str] = []



    def log_event(self, msg: str):

        timestamp = datetime.now().strftime("%H:%M:%S")

        entry = f"[{timestamp}] {msg}"

        self.logs.append(entry)

        if len(self.logs) > 200:

            self.logs.pop(0)

        logger.info(msg)



    def start_monitoring(self, group_name: str, batch_interval_minutes: Optional[int] = None):

        if self.is_running:

            return

        

        if batch_interval_minutes is not None:
            self.batch_interval_minutes = max(1, batch_interval_minutes)

        self.is_running = True

        # Đặt thời gian để vòng lặp đầu tiên tự động đẩy ngay các tin tồn đọng lên Sheet
        self.last_batch_sync_time = time.time() - (self.batch_interval_minutes * 60)

        

        self.monitored_group_name = group_name
        zalo_web_adapter.select_group(group_name)
        zalo_web_adapter.is_monitoring = True

        

        self.log_event(f"Bắt đầu giám sát Group '{group_name}' (Chu kỳ tự động đẩy Google Sheet: {self.batch_interval_minutes} phút)")



    def stop_monitoring(self):

        self.is_running = False

        zalo_web_adapter.is_monitoring = False

        self.log_event("Đã dừng giám sát Zalo.")



    def process_and_store_messages(self, messages: List[Dict[str, Any]]) -> int:

        """

        Xử lý danh sách tin nhắn từ Zalo:

        - Nếu tin nhắn có Quote (trả lời tin khác): gom vào thread của tin nhắn gốc dạng cây:

          [10:00] Nguyễn Văn A: Cửa hàng ABC camera 03 bị mất hình

          ↳ [10:05] Trần Văn B: Đang kiểm tra nguồn switch

        - Nếu không có Quote: lưu độc lập thành tin nhắn gốc mới.

        """

        if not messages:

            return 0



        inserted_count = 0

        for m in messages:

            text = m.get("content") or m.get("text") or ""

            sender = m.get("sender") or "Thành viên"

            group_name = m.get("group_name") or "Zalo Group"

            sent_time = m.get("time_str") or m.get("time") or ""

            msg_hash = m.get("hash")

            quote_data = m.get("quote")



            if quote_data and isinstance(quote_data, dict) and quote_data.get("text"):

                q_text = quote_data.get("text", "").strip()

                q_sender = quote_data.get("sender", "").strip()
                if q_sender and q_text.lower().startswith(q_sender.lower()):
                    q_text = q_text[len(q_sender):].strip()
                root = find_matching_root_message(group_name, q_text, q_sender)

                # Kiểm tra thông minh: Quote lại tin nhắn nhưng nội dung trả lời để xử lý một mã shop mới khác
                root_shop_code = extract_store_code(q_text)
                reply_shop_code = extract_store_code(text)
                is_different_shop = bool(reply_shop_code and root_shop_code and reply_shop_code != root_shop_code)

                if root and not is_different_shop:
                    # Cùng shop hoặc tin phản hồi cập nhật thông thường -> Ghép vào luồng tin gốc
                    appended = append_reply_to_thread(
                        root_id=root["id"],
                        reply_sender=sender,
                        reply_time=sent_time,
                        reply_text=text,
                        reply_hash=msg_hash
                    )
                    save_reply_message(
                        msg_hash=msg_hash,
                        group_name=group_name,
                        sender=sender,
                        raw_content=text,
                        sent_at=sent_time,
                        thread_root_hash=root["msg_hash"],
                        quote_json=json.dumps(quote_data, ensure_ascii=False)
                    )
                    if appended:
                        inserted_count += 1

                else:

                    # Chưa có tin gốc trong DB -> Tạo luồng mới với tiền tố [Gốc]

                    time_disp = sent_time or "Ca"

                    if " " in time_disp:

                        time_disp = time_disp.split(" ")[-1][:5]

                    virtual_content = f"[Gốc] {q_sender or 'Thành viên'}: {q_text}\n↳ [{time_disp}] {sender}: {text}"

                    saved = save_raw_message(

                        msg_hash=msg_hash,

                        group_name=group_name,

                        sender=sender,

                        raw_content=virtual_content,

                        sent_at=sent_time,

                        quote_json=json.dumps(quote_data, ensure_ascii=False)

                    )

                    if saved:

                        inserted_count += 1

            else:

                saved = save_raw_message(

                    msg_hash=msg_hash,

                    group_name=group_name,

                    sender=sender,

                    raw_content=text,

                    sent_at=sent_time

                )

                if saved:

                    inserted_count += 1



        return inserted_count



    async def scan_history_messages(self, scroll_count: int = 5) -> Dict[str, Any]:

        """Đọc và quét toàn bộ tin nhắn trong Group (không bỏ sót tin nào)."""

        if not zalo_web_adapter.is_chat_open():

            self.log_event("Khung chat chưa mở trên Zalo Web. Vui lòng bấm mở nhóm chat trên màn hình Zalo.")

            return {"status": "error", "message": "Khung chat chưa mở trên Zalo Web", "total_scanned": 0, "inserted_count": 0}



        active_title = zalo_web_adapter.get_active_header_title() or zalo_web_adapter.active_group_name or "Group"

        self.log_event(f"Bắt đầu quét tin nhắn trong Group '{active_title}' (cuộn {scroll_count} lần để tải lịch sử)...")

        new_msgs = await asyncio.to_thread(zalo_web_adapter.fetch_new_messages, include_history=True, scroll_count=scroll_count)

        

        inserted_count = 0

        if new_msgs:

            inserted_count = self.process_and_store_messages(new_msgs)

            if inserted_count > 0:

                self.log_event(f"Đã quét được {len(new_msgs)} tin nhắn. Cập nhật gom luồng/thêm mới {inserted_count} sự vụ vào cơ sở dữ liệu.")

            else:

                self.log_event(f"Đã quét được {len(new_msgs)} tin nhắn trên màn hình (Tất cả đã đồng bộ đầy đủ trong cơ sở dữ liệu).")

        else:

            self.log_event(f"Không tìm thấy tin nhắn nào trong khung chat '{active_title}'.")



        # Xử lý ngay AI cho các tin nhắn đang PENDING (tối đa 200 tin)

        pending_ai = get_pending_ai_messages(limit=200)

        if pending_ai:

            self.log_event(f"Đang phân tích AI cho {len(pending_ai)} tin nhắn vừa quét...")

            for row in pending_ai:

                msg_id = row["id"]

                raw_text = row["raw_content"]

                sender = row["sender"]

                is_error, ai_dict, err_msg = await asyncio.to_thread(analyze_message_with_ai, raw_text, sender)

                update_ai_result(msg_id, is_error=is_error, ai_status="SUCCESS" if is_error else "SKIPPED", ai_result=ai_dict)



        # TỰ ĐỘNG ĐẨY NGAY LÊN GOOGLE SHEETS
        sync_res = await self.sync_pending_to_gsheet()
        self.last_batch_sync_time = time.time()

        return {"status": "ok", "total_scanned": len(new_msgs), "inserted_count": inserted_count, "sync_res": sync_res}



    async def run_loop_step(self):

        """Được gọi định kỳ bởi background worker mỗi 10-15 giây."""

        if not self.is_running:

            return



        try:
            # Tự động phát hiện và phục hồi nếu cửa sổ chat Zalo Web bị văng sang nhóm khác
            if hasattr(self, 'monitored_group_name') and self.monitored_group_name:
                cur_header = zalo_web_adapter.get_active_header_title()
                # Chỉ cảnh báo và chọn lại nhóm khi đọc được tiêu đề rõ ràng VÀ tiêu đề đó lệch khỏi nhóm cần theo dõi
                if cur_header and cur_header.strip():
                    is_match = (
                        self.monitored_group_name.lower() in cur_header.lower() or 
                        cur_header.lower() in self.monitored_group_name.lower()
                    )
                    if not is_match:
                        logger.warning(f"Phát hiện Zalo Web bị lệch nhóm (Hiện tại: '{cur_header}'). Tự động chọn lại nhóm '{self.monitored_group_name}'...")
                        await asyncio.to_thread(zalo_web_adapter.select_group, self.monitored_group_name)

            new_msgs = await asyncio.to_thread(zalo_web_adapter.fetch_new_messages, include_history=False)

            if new_msgs:

                upd_count = self.process_and_store_messages(new_msgs)

                self.log_event(f"Phát hiện {len(new_msgs)} tin nhắn mới (cập nhật gom luồng {upd_count} sự vụ).")



            pending_ai = get_pending_ai_messages(limit=10)

            if pending_ai:

                for row in pending_ai:

                    msg_id = row["id"]

                    raw_text = row["raw_content"]

                    sender = row["sender"]



                    is_error, ai_dict, err_msg = await asyncio.to_thread(analyze_message_with_ai, raw_text, sender)

                    update_ai_result(msg_id, is_error=is_error, ai_status="SUCCESS" if is_error else "SKIPPED", ai_result=ai_dict)



            elapsed = (time.time() - self.last_batch_sync_time) / 60.0

            if elapsed >= self.batch_interval_minutes:

                await self.sync_pending_to_gsheet()

                self.last_batch_sync_time = time.time()



        except Exception as e:

            logger.error(f"Lỗi trong vòng lặp giám sát Zalo: {e}", exc_info=True)

            self.log_event(f"[LỖI] {str(e)}")



    async def sync_pending_to_gsheet(self, force_reconcile: bool = False) -> Dict[str, Any]:

        """Thực hiện đồng bộ TOÀN BỘ tin nhắn sang Google Sheets (bao gồm cả tin lỗi và tin thông thường)."""

        if force_reconcile:

            sync_candidates = get_messages_for_gsheet_reconcile(limit=500)

        else:

            sync_candidates = get_pending_sync_messages(limit=500, sync_all=True)



        if not sync_candidates and not force_reconcile:

            self.log_event("Toàn bộ tin nhắn hiện có đã được đồng bộ lên Google Sheets.")

            return {"status": "ok", "synced_count": 0, "message": "Toàn bộ tin nhắn đã được đồng bộ"}



        self.log_event(f"Đang kiểm tra và đối soát {len(sync_candidates)} tin nhắn với Google Sheets...")



        cfg = get_config()

        gsheet_cfg = cfg.get("gsheet", {})
        zalo_cfg = cfg.get("zalo_monitor", {})

        spreadsheet_id = zalo_cfg.get("spreadsheet_id") or gsheet_cfg.get("spreadsheet_id")

        target_sheet_name = zalo_cfg.get("sheet_zalo_monitor") or gsheet_cfg.get("sheet_zalo_monitor", "Gs An Ninh")

        handover_sheet_name = zalo_cfg.get("sheet_zalo_handover") or gsheet_cfg.get("sheet_zalo_handover", "Zalo_Bao_Cao_Ca")

        max_handover_lines = zalo_cfg.get("handover_max_lines", 6)



        if not spreadsheet_id:

            msg = "Chưa cấu hình spreadsheet_id trong config.json"

            self.log_event(f"[LỖI SYNC] {msg}")

            return {"status": "error", "message": msg}



        try:

            def _do_sync():

                client = get_client()

                sh = client.open_by_key(spreadsheet_id)

                

                # 1. Sheet sự cố phát sinh tức thời

                try:

                    ws_monitor = sh.worksheet(target_sheet_name)

                except Exception:

                    ws_monitor = sh.add_worksheet(title=target_sheet_name, rows=2000, cols=15)

                    self.log_event(f"Đã tạo mới worksheet '{target_sheet_name}'")



                # 2. Sheet báo cáo ca nhiều dòng

                try:

                    ws_handover = sh.worksheet(handover_sheet_name)

                except Exception:

                    ws_handover = sh.add_worksheet(title=handover_sheet_name, rows=2000, cols=15)

                    self.log_event(f"Đã tạo mới worksheet '{handover_sheet_name}'")



                expected_headers = [
                    "Message_ID", "Detected_At", "Thời gian gửi", "Người gửi",
                    "Mã shop", "Nội dung", "Trạng thái", "Group_Name"
                ]



                def _ensure_headers(ws):

                    vals = ws.get_all_values()

                    has_header = False

                    if vals and len(vals) > 0:

                        first_row = vals[0]

                        if any(c.strip() for c in first_row) and "Message_ID" in first_row:

                            has_header = True

                    if not has_header:

                        ws.update(values=[expected_headers], range_name="A1:H1")

                        vals = [expected_headers]
                        try:
                            sh.batch_update({'requests': [{
                                'updateDimensionProperties': {
                                    'range': {'sheetId': ws.id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 2},
                                    'properties': {'hiddenByUser': True},
                                    'fields': 'hiddenByUser'
                                }
                            }]})
                        except Exception:
                            pass

                    id_to_row = {}
                    key_to_row = {}

                    if len(vals) > 1:
                        hdr = vals[0]
                        idx_id = hdr.index("Message_ID") if "Message_ID" in hdr else 0
                        idx_time = hdr.index("Thời gian gửi") if "Thời gian gửi" in hdr else 2
                        idx_sender = hdr.index("Người gửi") if "Người gửi" in hdr else 3
                        idx_shop = hdr.index("Mã shop") if "Mã shop" in hdr else 4

                        for row_num, row in enumerate(vals[1:], start=2):
                            if len(row) > idx_id and row[idx_id]:
                                id_to_row[row[idx_id].strip()] = row_num
                            
                            # Khóa chống trùng lặp: Thời gian gửi + Người gửi + Mã shop
                            if len(row) > max(idx_time, idx_sender, idx_shop):
                                r_time = row[idx_time].strip()
                                r_sender = re.sub(r'\s+', ' ', row[idx_sender].strip())
                                r_shop = row[idx_shop].strip()
                                if r_time and r_sender and r_shop:
                                    key_to_row[f"{r_time}_{r_sender}_{r_shop}"] = row_num

                    return id_to_row, key_to_row, len(vals)



                id_to_row_monitor, key_to_row_monitor, count_monitor = _ensure_headers(ws_monitor)

                id_to_row_handover, key_to_row_handover, count_handover = _ensure_headers(ws_handover)



                new_rows_monitor = []

                new_rows_handover = []

                updates_monitor = []

                updates_handover = []

                synced_msg_ids = []



                for item in sync_candidates:

                    m_id = item["msg_hash"]

                    raw_content = item["raw_content"]

                    is_handover = is_shift_handover_report(raw_content, max_lines=max_handover_lines)



                    if is_handover:

                        shop_code = extract_store_code(raw_content)
                        status_str = detect_incident_status(raw_content) or "Báo cáo giao ca"

                        if m_id in id_to_row_handover:
                            row_num = id_to_row_handover[m_id]
                            updates_handover.append({
                                "range": f"C{row_num}:G{row_num}",
                                "values": [[item["sent_at"] or "", item["sender"] or "", shop_code, raw_content, status_str]]
                            })
                            synced_msg_ids.append(item["id"])
                            continue

                        row_vals = [
                            m_id,
                            item["detected_at"],
                            item["sent_at"] or "",
                            item["sender"] or "",
                            shop_code,
                            raw_content,
                            status_str,
                            item["group_name"]
                        ]

                        new_rows_handover.append(row_vals)

                        synced_msg_ids.append(item["id"])

                    else:
                        # Tách các dòng sự vụ nếu tin nhắn chứa nhiều sự vụ / mã shop khác nhau
                        sub_incidents = split_multiline_incidents(raw_content)
                        for idx_sub, sub_txt in enumerate(sub_incidents):
                            sub_m_id = m_id if idx_sub == 0 else f"{m_id}_{idx_sub+1}"
                            sub_shop_code = extract_store_code(sub_txt)
                            cleaned_sub_txt = clean_content_remove_shop_code(sub_txt, sub_shop_code)
                            status_str = detect_incident_status(sub_txt)

                            inc_key = f"{item['sent_at'] or ''}_{re.sub(r'\s+', ' ', item['sender'] or '')}_{sub_shop_code}"
                            target_row = id_to_row_monitor.get(sub_m_id) or (key_to_row_monitor.get(inc_key) if sub_shop_code else None)

                            if target_row:
                                updates_monitor.append({
                                    "range": f"C{target_row}:G{target_row}",
                                    "values": [[item["sent_at"] or "", item["sender"] or "", sub_shop_code, cleaned_sub_txt, status_str]]
                                })
                            else:
                                row_vals = [
                                    sub_m_id,
                                    item["detected_at"],
                                    item["sent_at"] or "",
                                    item["sender"] or "",
                                    sub_shop_code,
                                    cleaned_sub_txt,
                                    status_str,
                                    item["group_name"]
                                ]
                                new_rows_monitor.append(row_vals)
                                if sub_shop_code:
                                    key_to_row_monitor[inc_key] = count_monitor + len(new_rows_monitor)

                        synced_msg_ids.append(item["id"])



                if new_rows_monitor:
                    start_r = count_monitor + 1
                    end_r = start_r + len(new_rows_monitor) - 1
                    ws_monitor.update(values=new_rows_monitor, range_name=f"A{start_r}:H{end_r}")

                if updates_monitor:
                    ws_monitor.batch_update(updates_monitor)

                if new_rows_handover:
                    start_r = count_handover + 1
                    end_r = start_r + len(new_rows_handover) - 1
                    ws_handover.update(values=new_rows_handover, range_name=f"A{start_r}:H{end_r}")

                if updates_handover:
                    ws_handover.batch_update(updates_handover)



                total_sheet_rows = (count_monitor - 1 + len(new_rows_monitor)) + (count_handover - 1 + len(new_rows_handover))

                total_actions = len(new_rows_monitor) + len(new_rows_handover) + len(updates_monitor) + len(updates_handover)

                return total_actions, len(new_rows_monitor), len(updates_monitor), synced_msg_ids, total_sheet_rows



            new_count, m_new, m_upd, msg_ids, total_rows = await asyncio.to_thread(_do_sync)

            mark_messages_synced(msg_ids, sync_status="SYNCED")



            if new_count > 0:

                self.log_event(f"Đã đồng bộ lên Sheet: {m_new} dòng mới, cập nhật {m_upd} luồng phản hồi. Tổng cộng {total_rows} bản ghi.")

            else:

                self.log_event(f"Toàn bộ tin nhắn ({total_rows} tin) đã có sẵn đầy đủ trên 2 tab Google Sheets, không cần ghi thêm.")



            return {"status": "ok", "synced_count": new_count, "total_on_sheet": total_rows}



        except Exception as e:

            logger.error(f"Lỗi khi đồng bộ Google Sheets: {e}", exc_info=True)

            self.log_event(f"[LỖI SYNC] {str(e)}")

            mark_messages_synced([i["id"] for i in sync_candidates], sync_status="FAILED", error_msg=str(e))

            return {"status": "error", "message": str(e)}



    def clear_history_data(self, clear_db: bool = True, clear_sheet: bool = True) -> Dict[str, Any]:

        """Xóa sạch các bản quét cũ bị nhiễu để bắt đầu quét mới từ đầu."""

        if clear_db:

            clear_all_messages()

            zalo_web_adapter.seen_hashes.clear()

            zalo_web_adapter.baseline_established = False

            self.log_event("Đã xóa sạch toàn bộ lịch sử tin nhắn trong cơ sở dữ liệu cục bộ.")



        if clear_sheet:

            try:

                cfg = get_config()
                gsheet_cfg = cfg.get("gsheet", {})
                zalo_cfg = cfg.get("zalo_monitor", {})

                spreadsheet_id = zalo_cfg.get("spreadsheet_id") or gsheet_cfg.get("spreadsheet_id")

                sheet_monitor = zalo_cfg.get("sheet_zalo_monitor") or gsheet_cfg.get("sheet_zalo_monitor", "Gs An Ninh")

                sheet_handover = zalo_cfg.get("sheet_zalo_handover") or gsheet_cfg.get("sheet_zalo_handover", "Zalo_Bao_Cao_Ca")

                if spreadsheet_id:

                    client = get_client()

                    sh = client.open_by_key(spreadsheet_id)

                    expected_headers = [
                        "Message_ID", "Detected_At", "Thời gian gửi", "Người gửi",
                        "Mã shop", "Nội dung", "Trạng thái", "Group_Name"
                    ]

                    for s_name in [sheet_monitor, sheet_handover]:

                        try:

                            ws = sh.worksheet(s_name)

                            ws.clear()

                            ws.update(values=[expected_headers], range_name="A1:H1")

                            self.log_event(f"Đã làm sạch trang tính '{s_name}', chỉ giữ lại hàng tiêu đề.")

                        except Exception as e:

                            self.log_event(f"Lỗi khi làm sạch trang tính '{s_name}': {e}")

            except Exception as ex:

                logger.warning(f"Lỗi clear Google Sheets: {ex}")



        return {"status": "ok", "message": "Đã xóa sạch dữ liệu quét cũ và làm mới Google Sheets thành công."}



    def get_full_state(self, include_messages: bool = True) -> Dict[str, Any]:

        adapter_status = zalo_web_adapter.get_status()

        stats = get_monitor_stats()

        formatted_items = []

        if include_messages:

            recent_items = get_recent_messages(limit=50)

            for r in recent_items:

                item_dict = dict(r)

                if item_dict.get("ai_result_json"):

                    try:

                        item_dict["ai_result"] = json.loads(item_dict["ai_result_json"])

                    except Exception:

                        item_dict["ai_result"] = None

                formatted_items.append(item_dict)



        return {

            "is_monitoring": self.is_running,

            "batch_interval_minutes": self.batch_interval_minutes,

            "adapter_status": adapter_status,

            "stats": stats,

            "recent_messages": formatted_items,

            "logs": self.logs[-50:]

        }



# Singleton instance

zalo_monitor_service = ZaloMonitorService()

