"""
Vaccine Excel importer (pure, no database access).

    bytes -> VaccineSpreadsheetParser -> pick worksheet -> VaccineColumnMapper
          -> VaccineValidator -> in-file duplicate detection -> ImportAnalysis

Persistence (preview job, commit, DB duplicate check) lives in
``VaccineImportService``.
"""
from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.schemas.ticket import CHAIN_VACCINE
from app.services.vaccine.mapper import (
    VACCINE_COLUMNS,
    HeaderMapping,
    VaccineColumnMapper,
    VaccineMappedRow,
)
from app.services.vaccine.parser import (
    VaccineParseError,
    VaccineSpreadsheetParser,
    ParsedSheet,
)
from app.services.vaccine.validator import (
    STATUS_ERROR,
    STATUS_VALID,
    STATUS_WARNING,
    VaccineValidator,
    RowValidation,
)

PREFERRED_SHEET_NAME = "SHEET 1"


def build_dedup_key(chain: str, ticket_id: Optional[str], error_type: Optional[str],
                    error_description: Optional[str]) -> str:
    """Identity of one Vaccine violation.

    One MÃ YÊU CẦU can legitimately contain several violations (the real
    export has 59 request IDs spanning 2–4 rows, each with a different
    LOẠI LỖI / MÔ TẢ LỖI / HÌNH LỖI). Keying on ``chain + MÃ YÊU CẦU`` alone
    would silently drop those violations, so the key is
    ``chain + MÃ YÊU CẦU + LOẠI LỖI + MÔ TẢ LỖI`` (same identity idea as the
    existing FPT ``TicketDeduplicator``: ticket_id + error_type + error_reason).
    Values are NFC-normalized and whitespace-collapsed only for hashing; the
    stored values remain verbatim.
    """
    def norm(v: Optional[str]) -> str:
        return " ".join(unicodedata.normalize("NFC", v or "").split())

    payload = "\x1f".join([norm(chain), norm(ticket_id), norm(error_type), norm(error_description)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class AnalyzedRow:
    mapped: VaccineMappedRow
    validation: RowValidation
    dedup_key: str
    duplicate_of: Optional[int] = None  # row number of the first occurrence in this file

    @property
    def status(self) -> str:
        return self.validation.status

    @property
    def is_committable(self) -> bool:
        return self.validation.is_committable and self.duplicate_of is None


@dataclass
class ImportAnalysis:
    chain: str
    file_name: str
    file_format: str
    sheet_name: str
    available_sheets: List[str]
    header_row_number: int
    headers: List[str]
    header_mapping: HeaderMapping
    rows: List[AnalyzedRow] = field(default_factory=list)

    # ---- aggregates
    @property
    def total_rows(self) -> int:
        return len(self.rows)

    def _count(self, status: str) -> int:
        return sum(1 for r in self.rows if r.status == status)

    @property
    def valid_rows(self) -> int:
        return self._count(STATUS_VALID)

    @property
    def warning_rows(self) -> int:
        return self._count(STATUS_WARNING)

    @property
    def error_rows(self) -> int:
        return self._count(STATUS_ERROR)

    @property
    def duplicate_in_file_rows(self) -> int:
        return sum(1 for r in self.rows if r.duplicate_of is not None)

    @property
    def committable_rows(self) -> List[AnalyzedRow]:
        return [r for r in self.rows if r.is_committable]

    @property
    def validation_errors(self) -> List[Dict[str, Any]]:
        return [e for r in self.rows for e in r.validation.errors]

    @property
    def warnings(self) -> List[Dict[str, Any]]:
        return [w for r in self.rows for w in r.validation.warnings]


class VaccineExcelImporter:
    def __init__(self) -> None:
        self.parser = VaccineSpreadsheetParser()
        self.mapper = VaccineColumnMapper()
        self.validator = VaccineValidator()

    def analyze(self, content: bytes, file_name: str = "") -> ImportAnalysis:
        workbook = self.parser.parse(content)
        sheet, mapping = self._select_sheet(workbook.sheets)

        analysis = ImportAnalysis(
            chain=CHAIN_VACCINE,
            file_name=file_name,
            file_format=workbook.file_format,
            sheet_name=sheet.name,
            available_sheets=[s.name for s in workbook.sheets],
            header_row_number=sheet.header_row_number,
            headers=sheet.headers,
            header_mapping=mapping,
        )

        first_seen: Dict[str, int] = {}
        for prow in sheet.rows:
            mapped = self.mapper.map_row(prow.row_number, prow.values, mapping)
            validation = self.validator.validate(mapped)
            key = build_dedup_key(CHAIN_VACCINE, mapped.ticket_id, mapped.error_type, mapped.error_description)
            arow = AnalyzedRow(mapped=mapped, validation=validation, dedup_key=key)

            # In-file duplicates only matter for rows that would be committed.
            if validation.is_committable:
                if key in first_seen:
                    arow.duplicate_of = first_seen[key]
                    self.validator.mark_duplicate_in_file(validation, first_seen[key], mapped.ticket_id)
                else:
                    first_seen[key] = prow.row_number
            analysis.rows.append(arow)
        return analysis

    def _select_sheet(self, sheets: List[ParsedSheet]) -> "tuple[ParsedSheet, HeaderMapping]":
        """Pick the worksheet whose header best matches the Vaccine layout.

        Preference: fewest missing required headers, then most matched
        headers, then the sheet named "SHEET 1", then workbook order.
        """
        best = None
        for order, sheet in enumerate(sheets):
            mapping = self.mapper.map_headers(sheet.headers)
            score = (
                len(mapping.missing_required),
                -len(mapping.field_to_index),
                0 if sheet.name.strip().upper() == PREFERRED_SHEET_NAME else 1,
                order,
            )
            if best is None or score < best[0]:
                best = (score, sheet, mapping)

        assert best is not None  # parser guarantees >= 1 sheet
        _, sheet, mapping = best
        if not sheet.headers:
            raise VaccineParseError(f"Worksheet '{sheet.name}' không có dữ liệu.")
        if mapping.missing_required:
            raise VaccineParseError(
                "File không đúng mẫu báo cáo Vaccine. Thiếu cột bắt buộc: "
                + ", ".join(mapping.missing_required)
                + f". (Worksheet '{sheet.name}', tìm thấy {len(mapping.field_to_index)}/{len(VACCINE_COLUMNS)} cột)"
            )
        return sheet, mapping
