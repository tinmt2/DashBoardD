from typing import Dict, Any
from datetime import datetime

class ValidatorResult:
    def __init__(self):
        self.is_valid = True
        self.errors = [] # list of dicts: {"row_number": int, "field": str, "value": Any, "reason": str}

class RecordValidator:
    def validate(self, row_idx: int, record: Dict[str, Any]) -> ValidatorResult:
        result = ValidatorResult()

        def add_error(field, value, reason):
            result.is_valid = False
            result.errors.append({
                "row_number": row_idx,
                "field": field,
                "value": value,
                "reason": reason
            })

        if not record.get("ticket_id"):
            add_error("ticket_id", record.get("ticket_id"), "Missing required value")

        if not record.get("employee_name"):
            add_error("employee_name", record.get("employee_name"), "Missing required value")

        error_status = record.get("error_status")
        if error_status not in ["ERROR", "PASS", "PENDING"]:
            add_error("error_status", error_status, "Must be ERROR, PASS, or PENDING")

        if record.get("chain") != "FPT_SHOP":
            add_error("chain", record.get("chain"), "Must be FPT_SHOP")
            
        if record.get("source") != "EXCEL":
            add_error("source", record.get("source"), "Must be EXCEL")
            
        if record.get("created_at") is not None and not isinstance(record.get("created_at"), datetime):
            add_error("created_at", record.get("created_at"), "Must be a valid datetime or None")
            
        return result
