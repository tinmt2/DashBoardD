"""
Vaccine row validation.

Each row is classified as ``valid`` / ``warning`` / ``error``:

ERROR (row is NOT committed)
  * missing / malformed MÃ YÊU CẦU
  * missing NHÓM YÊU CẦU, MÃ SHOP, TÊN SHOP, LOẠI LỖI, MÔ TẢ LỖI
  * missing or unparseable NGÀY YÊU CẦU
WARNING (row IS committed)
  * missing NHÂN VIÊN VI PHẠM (employee stays null – never inferred)
  * missing HÌNH LỖI, or a token in HÌNH LỖI that is not an http(s) URL
  * unparseable optional fields (NGÀY DỰ KIẾN HOÀN THÀNH, SỐ CAMERA)
  * ambiguous employee cell (several employees)
  * row duplicated earlier in the same file (skipped at commit)

Rationale for the required list: it is the minimum needed to build a
meaningful, de-duplicable ``TicketRecord`` (ticket id + error identity + shop +
date). Employee is intentionally *not* required for Vaccine, unlike FPT Shop.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.services.vaccine.mapper import FIELD_TO_HEADER, VaccineMappedRow

STATUS_VALID = "valid"
STATUS_WARNING = "warning"
STATUS_ERROR = "error"

# Observed IDs are 8 digits ("06977563"). Allow alnum plus - _ . / to be
# future-proof, but no whitespace and a sane length.
REQUEST_ID_PATTERN = re.compile(r"^[0-9A-Za-z][0-9A-Za-z\-_./]{0,49}$")

REQUIRED_FIELDS = [
    "ticket_id",
    "request_group",
    "store_code",
    "store_name",
    "error_type",
    "error_description",
    "requested_date",
]


@dataclass
class RowValidation:
    row_number: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.errors:
            return STATUS_ERROR
        if self.warnings:
            return STATUS_WARNING
        return STATUS_VALID

    @property
    def is_committable(self) -> bool:
        return not self.errors


class VaccineValidator:
    def validate(self, row: VaccineMappedRow) -> RowValidation:
        result = RowValidation(row_number=row.row_number)

        def issue(bucket: List[Dict[str, Any]], field_name: str, value: Any, reason: str, severity: str) -> None:
            bucket.append({
                "rowNumber": row.row_number,
                "field": field_name,
                "column": FIELD_TO_HEADER.get(field_name, field_name),
                "value": value,
                "reason": reason,
                "severity": severity,
            })

        def error(field_name: str, value: Any, reason: str) -> None:
            issue(result.errors, field_name, value, reason, STATUS_ERROR)

        def warning(field_name: str, value: Any, reason: str) -> None:
            issue(result.warnings, field_name, value, reason, STATUS_WARNING)

        # Parse-level issues from the mapper (dates, numbers, employee ambiguity)
        parse_error_fields = set()
        for pi in row.issues:
            if pi.severity == STATUS_ERROR:
                error(pi.field, pi.value, pi.reason)
                parse_error_fields.add(pi.field)
            else:
                warning(pi.field, pi.value, pi.reason)

        # Required fields
        for name in REQUIRED_FIELDS:
            if name in parse_error_fields:
                continue
            if getattr(row, name) in (None, ""):
                error(name, None, f"Thiếu {FIELD_TO_HEADER[name]}")

        if row.ticket_id and not REQUEST_ID_PATTERN.match(row.ticket_id):
            error("ticket_id", row.ticket_id, "MÃ YÊU CẦU không hợp lệ (chỉ gồm chữ/số, không khoảng trắng)")

        # Soft checks
        if not row.employee_raw:
            warning("employee", None, "Chưa có NHÂN VIÊN VI PHẠM (để trống, không tự gán)")

        if not row.evidence_urls:
            warning("evidence_url", None, "Thiếu HÌNH LỖI")
        else:
            bad = [u for u in row.evidence_urls if not u.lower().startswith(("http://", "https://"))]
            if bad:
                warning("evidence_url", ", ".join(bad), "HÌNH LỖI có giá trị không phải URL http(s)")

        return result

    @staticmethod
    def mark_duplicate_in_file(result: RowValidation, first_row_number: int, ticket_id: Any) -> None:
        result.warnings.append({
            "rowNumber": result.row_number,
            "field": "ticket_id",
            "column": FIELD_TO_HEADER["ticket_id"],
            "value": ticket_id,
            "reason": (
                f"Trùng MÃ YÊU CẦU + LOẠI LỖI + MÔ TẢ LỖI với dòng {first_row_number} "
                "trong file (sẽ bỏ qua khi commit)"
            ),
            "severity": STATUS_WARNING,
        })
