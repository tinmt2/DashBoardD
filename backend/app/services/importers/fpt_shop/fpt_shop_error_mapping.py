import re
from typing import Optional

class FPTShopErrorMapping:
    def __init__(self):
        self.rules = {
            "thiếu thông tin": "Thiếu thông tin",
            "thiếu tt": "Thiếu thông tin",
            "missing information": "Thiếu thông tin",
            
            "sai nội dung": "Sai nội dung",
            "sai nd": "Sai nội dung",
            
            "sai phân loại": "Sai phân loại",
            "sai pl": "Sai phân loại",
            
            "sai quy trình": "Sai quy trình",
            "sai qt": "Sai quy trình",
            
            "thiếu bằng chứng": "Thiếu bằng chứng",
            "thiếu bc": "Thiếu bằng chứng",
            
            "khác": "Khác",
        }

    def normalize(self, raw_error: Optional[str]) -> Optional[str]:
        if not raw_error or str(raw_error).strip() == "" or str(raw_error).lower() == "nan":
            return None
        
        normalized = str(raw_error).lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        if normalized in self.rules:
            return self.rules[normalized]
            
        # If not known, we just return the original error string
        # FPT Shop uses specific error types like "Khóa cửa", "Phát video quảng cáo..."
        return str(raw_error).strip()