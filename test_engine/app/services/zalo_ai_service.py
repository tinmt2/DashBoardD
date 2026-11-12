import os
import sys
import re
import json
import logging
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from app.config import get_config

logger = logging.getLogger(__name__)

# Heuristic error keywords
ERROR_KEYWORDS = [
    "mkn", "mất kết nối", "mat ket noi", "lỗi", "loi", "hỏng", "hong",
    "không lên", "khong len", "mất tín hiệu", "mat tin hieu", "đen màn", "den man",
    "chết cam", "chet cam", "không xem được", "khong xem duoc", "rớt mạng", "rot mang",
    "camera", "đầu ghi", "dau ghi", "dvr", "nvr", "ổ cứng", "o cung",
    "hư", "sự cố", "su co", "nhờ kiểm tra", "nho kiem tra", "nhờ hỗ trợ", "nho ho tro",
    "check giúp", "check giup", "xử lý giúp", "xu ly giup", "ticket",
    "trộm", "trom", "đột nhập", "dot nhap", "báo động", "bao dong",
    "mất điện", "mat dien", "cúp điện", "cup dien", "két", "ket",
    "hồng ngoại", "hong ngoai", "cụp", "cup", "lệch", "lech", "natport"
]

class ExtractedError(BaseModel):
    is_error: bool = Field(description="Tin nhắn có phản ánh hoặc báo cáo sự cố kỹ thuật hay không")
    chain: Optional[str] = Field(default="Long Châu", description="Chuỗi cửa hàng, ví dụ: Long Châu, FPT Shop")
    store_name: Optional[str] = Field(default=None, description="Tên cửa hàng, ví dụ: 274B Khương Trung, Nguyễn Trãi")
    store_code: Optional[str] = Field(default=None, description="Mã cửa hàng số nếu có, ví dụ: 80226, 81230")
    system_type: Optional[str] = Field(default=None, description="Hệ thống bị lỗi: Camera, Đầu ghi, Mạng/Internet, Màn hình, Khác")
    error_location: Optional[str] = Field(default=None, description="Vị trí thiết bị: Quầy thu ngân, Cửa chính, Kho, Tầng 1...")
    clean_summary: str = Field(description="Mô tả lỗi ngắn gọn, súc tích, văn phong kỹ thuật rõ ràng")
    occurred_time: Optional[str] = Field(default=None, description="Thời điểm lỗi phát sinh nếu có đề cập, ví dụ: sáng nay, từ tối qua")
    priority: Optional[str] = Field(default="Bình thường", description="Mức độ ưu tiên: Thấp, Bình thường, Cao, Khẩn cấp")
    confidence: float = Field(default=1.0, description="Độ tin cậy từ 0.0 đến 1.0")

def quick_heuristic_check(text: str) -> bool:
    if not text or len(text.strip()) < 5:
        return False
    lower_text = text.lower()
    for kw in ERROR_KEYWORDS:
        if kw in lower_text:
            return True
    return False

_warned_gemini_key = False

def get_gemini_api_key() -> Optional[str]:
    cfg = get_config()
    zalo_cfg = cfg.get("zalo_monitor", {})
    key = zalo_cfg.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
    return key

def analyze_message_with_ai(raw_text: str, sender: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Phân tích tin nhắn bằng Google Gemini API.
    Trả về (is_error, result_dict, error_msg).
    """
    global _warned_gemini_key

    # 1. Heuristic check first
    is_candidate = quick_heuristic_check(raw_text)
    if not is_candidate:
        return False, None, None

    api_key = get_gemini_api_key()
    if not api_key:
        # Nếu chưa cấu hình API key, fallback dùng heuristic rule đơn giản (chỉ cảnh báo 1 lần)
        if not _warned_gemini_key:
            logger.info("GEMINI_API_KEY chưa được cấu hình. Hệ thống sử dụng heuristic fallback extraction.")
            _warned_gemini_key = True
        fallback_data = {
            "is_error": True,
            "chain": "Long Châu",
            "store_name": "Chưa xác định",
            "store_code": None,
            "system_type": "Camera / Kỹ thuật",
            "error_location": "Chưa xác định",
            "clean_summary": raw_text.strip(),
            "occurred_time": "Chưa xác định",
            "priority": "Bình thường",
            "confidence": 0.7,
            "note": "Heuristic fallback (chưa nhập Gemini API Key)"
        }
        return True, fallback_data, None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt = f"""Bạn là chuyên viên IT Helpdesk và giám sát kỹ thuật chuỗi nhà thuốc Long Châu.
Nhiệm vụ của bạn là đọc tin nhắn báo cáo từ nhân viên trong nhóm chat Zalo và trích xuất thông tin lỗi kỹ thuật theo cấu trúc JSON chuẩn.

QUY TẮC BẮT BUỘC (ANTI-HALLUCINATION):
1. Chỉ trích xuất thông tin có thật trong tin nhắn.
2. KHÔNG TỰ BỊA ĐẶT mã shop, tên đường, thời gian hoặc thiết bị nếu tin nhắn không nhắc đến.
3. Nếu không có mã shop, hãy để store_code là null.
4. clean_summary phải viết lại lỗi một cách chuyên nghiệp, rõ ràng, chuẩn tiếng Việt có dấu.
5. Nếu tin nhắn chỉ là hỏi thăm, chào hỏi, hoặc nội dung không phải lỗi kỹ thuật, hãy đặt is_error = false.

Tin nhắn cần phân tích:
Người gửi: {sender or 'Nhân viên'}
Nội dung: "{raw_text}"
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedError,
                temperature=0.1
            ),
        )

        result_json = json.loads(response.text)
        is_error = result_json.get("is_error", False)
        return is_error, result_json, None

    except Exception as e:
        logger.error(f"Lỗi khi gọi Gemini API: {e}", exc_info=True)
        # Fallback to heuristic result so message is not lost
        fallback_data = {
            "is_error": True,
            "chain": "Long Châu",
            "store_name": "Chưa xác định",
            "store_code": None,
            "system_type": "Camera / Kỹ thuật",
            "error_location": "Chưa xác định",
            "clean_summary": raw_text.strip(),
            "occurred_time": "Chưa xác định",
            "priority": "Bình thường",
            "confidence": 0.5,
            "error_detail": str(e)
        }
        return True, fallback_data, f"Gemini API error: {str(e)}"
