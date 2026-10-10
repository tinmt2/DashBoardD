import re
from typing import Dict, Any, List

class ColumnMapper:
    def __init__(self):
        # target_field -> list of aliases
        self.aliases = {
            "employee_name": ["người yêu cầu", "nguoi yeu cau", "người tạo", "nguoi tao", "người kiểm tra", "nguoi kiem tra", "nhân viên vi phạm", "tên nhân viên", "nhân viên", "employee name"],
            "ticket_id": ["mã ticket", "ticket", "ticket id", "mã yêu cầu", "ma yeu cau", "id"],
            "shop_code": ["mã shop", "shop code", "ma shop", "mã cửa hàng"],
            "created_at": ["ngày yêu cầu", "ngay yeu cau", "ngày tạo", "thời gian tạo", "created at", "thời gian"],
            "error_type": ["loại lỗi", "error type", "loai loi", "nhóm lỗi"],
            "error_reason": ["mô tả lỗi", "mo ta loi", "nội dung lỗi", "lý do lỗi", "error reason", "chi tiết lỗi", "hình lỗi"],
            "ticket_status": ["trạng thái", "trang thai", "status"],
            "note": ["ghi chú", "ghi chu", "note"]
        }

    def normalize_column_name(self, col_name: str) -> str:
        if not col_name:
            return ""
        # Convert to lower case
        col_name = str(col_name).lower().strip()
        # Remove multiple spaces
        col_name = re.sub(r'\s+', ' ', col_name)
        return col_name

    def map_columns(self, headers: List[str]) -> Dict[str, Any]:
        mapping_result = {}
        matched_targets = set()

        for idx, original_header in enumerate(headers):
            if original_header is None:
                continue
            norm_header = self.normalize_column_name(original_header)
            if not norm_header:
                continue

            best_match = None
            best_confidence = 0.0

            for target_field, alias_list in self.aliases.items():
                if target_field in matched_targets:
                    continue
                
                # Exact normalized match
                if norm_header in alias_list:
                    best_match = target_field
                    best_confidence = 1.0
                    break
                
                # Partial match (low confidence)
                for alias in alias_list:
                    if alias in norm_header or norm_header in alias:
                        if 0.5 > best_confidence:
                            best_match = target_field
                            best_confidence = 0.5

            if best_match:
                # If there's already a mapping for this target field, we only override if confidence is strictly higher
                if best_match in mapping_result:
                    if best_confidence > mapping_result[best_match]["confidence"]:
                        mapping_result[best_match] = {
                            "source_column": original_header,
                            "confidence": best_confidence,
                            "index": idx
                        }
                else:
                    mapping_result[best_match] = {
                        "source_column": original_header,
                        "confidence": best_confidence,
                        "index": idx
                    }
                
                if best_confidence == 1.0:
                    matched_targets.add(best_match)

        return mapping_result