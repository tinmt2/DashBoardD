"""
LongChâu column mapping: Excel header -> domain field, and raw row -> normalized row.

Header matching is **exact** after normalization (Unicode NFC, upper-case,
collapsed whitespace), with an accent-insensitive fallback. There is no fuzzy
/ partial matching on purpose: LongChâu has look-alike headers such as
``TRẠNG THÁI`` vs ``TRẠNG THÁI BƯỚC`` and ``NGƯỜI YÊU CẦU`` vs
``NHÂN VIÊN VI PHẠM`` that must never be confused (the FPT mapper's partial
matching would map ``NGƯỜI YÊU CẦU`` to employee, which is wrong for LongChâu).
"""
from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.schemas.ticket import CHAIN_LONG_CHAU, TicketRecord
from app.services.long_chau.date_parser import LongChauDateParser
from app.services.long_chau.error_mapper import LongChauErrorMapper


@dataclass(frozen=True)
class ColumnSpec:
    field: str
    header: str
    required: bool  # header must exist in the file


# Order == order in the official LongChâu export (20 columns).
LONG_CHAU_COLUMNS: List[ColumnSpec] = [
    ColumnSpec("ticket_id", "MÃ YÊU CẦU", True),
    ColumnSpec("request_group", "NHÓM YÊU CẦU", True),
    ColumnSpec("requester", "NGƯỜI YÊU CẦU", False),
    ColumnSpec("handler_department", "SHOP/PHÒNG BAN XỬ LÝ", False),
    ColumnSpec("approver", "NGƯỜI DUYỆT", False),
    ColumnSpec("expected_completion_date", "NGÀY DỰ KIẾN HOÀN THÀNH", False),
    ColumnSpec("status", "TRẠNG THÁI", False),
    ColumnSpec("step", "BƯỚC", False),
    ColumnSpec("store_code", "MÃ SHOP", True),
    ColumnSpec("store_name", "TÊN SHOP", True),
    ColumnSpec("region", "VÙNG MIỀN SHOP", False),
    ColumnSpec("asm", "ASM SHOP", False),
    ColumnSpec("camera_count", "SỐ CAMERA", False),
    ColumnSpec("evidence_url", "HÌNH LỖI", False),
    ColumnSpec("error_type", "LOẠI LỖI", True),
    ColumnSpec("error_description", "MÔ TẢ LỖI", True),
    ColumnSpec("employee", "NHÂN VIÊN VI PHẠM", False),
    ColumnSpec("note", "GHI CHÚ", False),
    ColumnSpec("requested_date", "NGÀY YÊU CẦU", True),
    ColumnSpec("step_status", "TRẠNG THÁI BƯỚC", False),
]
FIELD_TO_HEADER: Dict[str, str] = {c.field: c.header for c in LONG_CHAU_COLUMNS}


def normalize_header(value: Any) -> str:
    text = unicodedata.normalize("NFC", "" if value is None else str(value))
    return re.sub(r"\s+", " ", text).strip().upper()


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.replace("Đ", "D").replace("đ", "d"))
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


_EXACT = {normalize_header(c.header): c for c in LONG_CHAU_COLUMNS}
_UNACCENTED = {strip_accents(normalize_header(c.header)): c for c in LONG_CHAU_COLUMNS}

# "50172 - Ngô Thị Mai Phương"  (format observed in the real LongChâu export)
_EMPLOYEE_PATTERN = re.compile(r"^(?P<id>\d{3,})\s*-\s*(?P<name>\S.*?)\s*$", re.DOTALL)
_EMPLOYEE_ID_TOKEN = re.compile(r"(?:^|[,;\n])\s*\d{3,}\s*-")
_URL_SPLIT = re.compile(r"[,;\s]+")


@dataclass
class HeaderMapping:
    field_to_index: Dict[str, int]
    column_mapping: List[Dict[str, Any]]
    missing_required: List[str]
    missing_optional: List[str]
    unknown_headers: List[str]
    duplicate_headers: List[str]


@dataclass
class FieldIssue:
    field: str
    value: Any
    reason: str
    severity: str  # "error" | "warning"


@dataclass
class LongChauMappedRow:
    row_number: int
    ticket_id: Optional[str] = None
    request_group: Optional[str] = None
    requester: Optional[str] = None
    handler_department: Optional[str] = None
    approver: Optional[str] = None
    expected_completion_date: Optional[date] = None
    status: Optional[str] = None
    step: Optional[str] = None
    store_code: Optional[str] = None
    store_name: Optional[str] = None
    region: Optional[str] = None
    asm: Optional[str] = None
    camera_count: Optional[str] = None
    evidence_url: Optional[str] = None  # original cell text (all URLs kept)
    evidence_urls: List[str] = field(default_factory=list)
    error_type: Optional[str] = None
    error_description: Optional[str] = None
    employee_raw: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    note: Optional[str] = None
    requested_date: Optional[datetime] = None
    step_status: Optional[str] = None
    # raw values of fields that failed parsing (for display)
    raw_requested_date: Any = None
    raw_ticket_id: Any = None
    issues: List[FieldIssue] = field(default_factory=list)


def _text(value: Any) -> Optional[str]:
    """Cell -> trimmed string (or None). Integral floats lose the '.0' suffix."""
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if value != value:  # NaN
            return None
        return str(int(value)) if value.is_integer() else str(value)
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y") if value.time() == datetime.min.time() else value.isoformat(sep=" ")
    text = str(value).strip()
    return text or None


class LongChauColumnMapper:
    def __init__(self) -> None:
        self.date_parser = LongChauDateParser()
        self.error_mapper = LongChauErrorMapper()

    # ---------------------------------------------------------------- headers
    def map_headers(self, headers: List[Any]) -> HeaderMapping:
        field_to_index: Dict[str, int] = {}
        column_mapping: List[Dict[str, Any]] = []
        unknown: List[str] = []
        duplicates: List[str] = []

        for idx, original in enumerate(headers):
            norm = normalize_header(original)
            if not norm:
                continue
            spec = _EXACT.get(norm)
            match_type = "exact"
            if spec is None:
                spec = _UNACCENTED.get(strip_accents(norm))
                match_type = "accent_insensitive"
            if spec is None:
                unknown.append(str(original))
                continue
            if spec.field in field_to_index:
                duplicates.append(str(original))  # keep first occurrence
                continue
            field_to_index[spec.field] = idx
            column_mapping.append({
                "field": spec.field,
                "sourceColumn": str(original),
                "expectedColumn": spec.header,
                "index": idx,
                "match": match_type,
            })

        missing_required = [c.header for c in LONG_CHAU_COLUMNS if c.required and c.field not in field_to_index]
        missing_optional = [c.header for c in LONG_CHAU_COLUMNS if not c.required and c.field not in field_to_index]
        return HeaderMapping(field_to_index, column_mapping, missing_required, missing_optional, unknown, duplicates)

    # ------------------------------------------------------------------- rows
    def map_row(self, row_number: int, values: List[Any], mapping: HeaderMapping) -> LongChauMappedRow:
        def raw(field_name: str) -> Any:
            idx = mapping.field_to_index.get(field_name)
            if idx is None or idx >= len(values):
                return None
            return values[idx]

        row = LongChauMappedRow(row_number=row_number)

        row.raw_ticket_id = raw("ticket_id")
        row.ticket_id = _text(row.raw_ticket_id)
        row.request_group = _text(raw("request_group"))
        row.requester = _text(raw("requester"))
        row.handler_department = _text(raw("handler_department"))
        row.approver = _text(raw("approver"))
        row.status = _text(raw("status"))
        row.step = _text(raw("step"))
        row.store_code = _text(raw("store_code"))
        row.store_name = _text(raw("store_name"))
        row.region = _text(raw("region"))
        row.asm = _text(raw("asm"))
        row.note = _text(raw("note"))
        row.step_status = _text(raw("step_status"))

        # Errors: verbatim (trim only)
        row.error_type = self.error_mapper.map_error_type(raw("error_type"))
        row.error_description = self.error_mapper.map_error_description(raw("error_description"))

        # Dates
        row.raw_requested_date = raw("requested_date")
        req = self.date_parser.parse(row.raw_requested_date)
        row.requested_date = req.value
        if req.error:
            row.issues.append(FieldIssue("requested_date", _text(row.raw_requested_date), req.error, "error"))

        exp_raw = raw("expected_completion_date")
        exp = self.date_parser.parse(exp_raw)
        row.expected_completion_date = exp.value.date() if exp.value else None
        if exp.error:
            # Non-required column -> warning, row is kept.
            row.issues.append(FieldIssue("expected_completion_date", _text(exp_raw), exp.error, "warning"))

        # Camera count
        cam_raw = raw("camera_count")
        row.camera_count = _text(cam_raw)

        # Evidence URLs (never downloaded; original string preserved)
        row.evidence_url = _text(raw("evidence_url"))
        row.evidence_urls = self.split_evidence_urls(row.evidence_url)

        # Employee (NHÂN VIÊN VI PHẠM only; never requester / ASM)
        row.employee_raw = _text(raw("employee"))
        row.employee_id, row.employee_name, emp_issue = self.parse_employee(row.employee_raw)
        if emp_issue:
            row.issues.append(FieldIssue("employee", row.employee_raw, emp_issue, "warning"))

        return row

    # --------------------------------------------------------------- helpers
    @staticmethod
    def split_evidence_urls(text: Optional[str]) -> List[str]:
        if not text:
            return []
        return [t for t in _URL_SPLIT.split(text) if t]

    @staticmethod
    def parse_employee(raw: Optional[str]) -> "tuple[Optional[str], Optional[str], Optional[str]]":
        """Split ``"<id> - <name>"`` only when the format is unambiguous.

        Returns ``(employee_id, employee_name, issue)``:
          * empty                       -> (None, None, None)
          * ``"50172 - Ngô Thị Mai Phương"`` -> ("50172", "Ngô Thị Mai Phương", None)
          * several employees in one cell -> (None, raw, warning)  (no guessing)
          * any other free text          -> (None, raw, None)     (kept as written)
        """
        if not raw:
            return None, None, None
        if len(_EMPLOYEE_ID_TOKEN.findall(raw)) > 1:
            return None, raw, "Ô NHÂN VIÊN VI PHẠM chứa nhiều nhân viên, chưa tách mã NV"
        m = _EMPLOYEE_PATTERN.match(raw)
        if m:
            return m.group("id"), m.group("name"), None
        return None, raw, None

    # ------------------------------------------------------- domain building
    def build_ticket_record(self, row: LongChauMappedRow, imported_at: datetime,
                            record_id: Optional[str] = None) -> TicketRecord:
        return TicketRecord(
            id=record_id or str(uuid.uuid4()),
            chain=CHAIN_LONG_CHAU,  # backend-enforced, never user input
            ticket_id=row.ticket_id or "",
            employee_id=row.employee_id,
            employee_name=row.employee_name,
            shop_code=row.store_code,
            shop_name=row.store_name,
            created_at=row.requested_date,
            checked_at=None,
            error_status=self.error_mapper.error_status(row.error_type),
            error_type=row.error_type,
            error_reason=row.error_description,
            ticket_status=row.status,
            note=row.note,
            source="EXCEL",
            imported_at=imported_at,
        )

    @staticmethod
    def build_detail(row: LongChauMappedRow) -> Dict[str, Any]:
        return {
            "request_group": row.request_group,
            "requester": row.requester,
            "handler_department": row.handler_department,
            "approver": row.approver,
            "expected_completion_date": row.expected_completion_date.isoformat() if row.expected_completion_date else None,
            "step": row.step,
            "region": row.region,
            "asm": row.asm,
            "camera_count": row.camera_count,
            "evidence_urls": row.evidence_url,
            "employee_raw": row.employee_raw,
            "requested_date": row.requested_date.date().isoformat() if row.requested_date else None,
            "step_status": row.step_status,
            "source_row": row.row_number,
        }

    @staticmethod
    def to_preview(row: LongChauMappedRow) -> Dict[str, Any]:
        """Normalized (post-mapping) row for the frontend preview."""
        return {
            "rowNumber": row.row_number,
            "chain": CHAIN_LONG_CHAU,
            "ticketId": row.ticket_id,
            "requestGroup": row.request_group,
            "requester": row.requester,
            "handlerDepartment": row.handler_department,
            "approver": row.approver,
            "expectedCompletionDate": row.expected_completion_date.isoformat() if row.expected_completion_date else None,
            "status": row.status,
            "step": row.step,
            "storeCode": row.store_code,
            "storeName": row.store_name,
            "region": row.region,
            "asm": row.asm,
            "cameraCount": row.camera_count,
            "evidenceUrl": row.evidence_url,
            "evidenceUrls": row.evidence_urls,
            "errorType": row.error_type,
            "errorDescription": row.error_description,
            "employeeRaw": row.employee_raw,
            "employeeId": row.employee_id,
            "employeeName": row.employee_name,
            "note": row.note,
            "requestedDate": row.requested_date.date().isoformat() if row.requested_date else None,
            "stepStatus": row.step_status,
        }
