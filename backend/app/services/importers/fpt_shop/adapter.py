import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from app.services.importers.fpt_shop.date_parser import FPTShopDateParser
from app.services.importers.fpt_shop.fpt_shop_error_mapping import FPTShopErrorMapping
import pandas as pd

class RowNormalizer:
    def __init__(self):
        self.date_parser = FPTShopDateParser()
        self.error_mapper = FPTShopErrorMapping()

    def get_value(self, row: Dict[str, Any], mapping: Dict[str, Any], field: str) -> Any:
        if field in mapping:
            col_name = mapping[field]["source_column"]
            val = row.get(col_name)
            if pd.isna(val) or val == "" or val is None:
                return None
            return val
        return None

    def normalize_row(self, row: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        raw_ticket = self.get_value(row, mapping, "ticket_id")
        ticket_id = str(raw_ticket).strip() if raw_ticket is not None else ""
        
        raw_emp = self.get_value(row, mapping, "employee_name")
        raw_emp_str = str(raw_emp).strip() if raw_emp is not None else ""
        
        employee_id = None
        employee_name = raw_emp_str
        
        if "--" in raw_emp_str:
            parts = raw_emp_str.split("--", 1)
            emp_id_part = parts[0].strip()
            emp_name_part = parts[1].strip()
            
            if emp_id_part:
                employee_id = emp_id_part
            if emp_name_part:
                employee_name = emp_name_part
        elif "-" in raw_emp_str:
            # Just in case they use a single dash
            parts = raw_emp_str.split("-", 1)
            emp_id_part = parts[0].strip()
            emp_name_part = parts[1].strip()
            # Ensure it looks like an ID (e.g. numeric) before trusting the split
            if emp_id_part.isdigit() and emp_name_part:
                employee_id = emp_id_part
                employee_name = emp_name_part
                
        raw_error_type = self.get_value(row, mapping, "error_type")
        error_type = self.error_mapper.normalize(raw_error_type)
        
        raw_created_at = self.get_value(row, mapping, "created_at")
        created_at = self.date_parser.parse(raw_created_at)

        # Infer error status based on error_type presence
        error_status = "ERROR" if error_type else "PASS"

        return {
            "id": str(uuid.uuid4()),
            "chain": "FPT_SHOP",
            "ticket_id": ticket_id,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "shop_code": str(self.get_value(row, mapping, "shop_code") or "").strip() or None,
            "shop_name": None,
            "created_at": created_at,
            "checked_at": None,
            "error_status": error_status,
            "error_type": error_type,
            "error_reason": str(self.get_value(row, mapping, "error_reason") or "").strip() or None,
            "ticket_status": str(self.get_value(row, mapping, "ticket_status") or "").strip() or None,
            "note": str(self.get_value(row, mapping, "note") or "").strip() or None,
            "source": "EXCEL",
            "imported_at": datetime.now(timezone.utc)
        }