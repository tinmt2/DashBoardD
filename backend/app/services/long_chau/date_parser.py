"""LongChâu date parsing (day-first, ``DD/MM/YYYY``)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional

_EXCEL_EPOCH = datetime(1899, 12, 30)
_DMY = re.compile(
    r"^(?P<d>\d{1,2})[/\-.](?P<m>\d{1,2})[/\-.](?P<y>\d{4})"
    r"(?:[ T](?P<H>\d{1,2}):(?P<M>\d{2})(?::(?P<S>\d{2}))?)?$"
)
_ISO = re.compile(
    r"^(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})"
    r"(?:[ T](?P<H>\d{1,2}):(?P<M>\d{2})(?::(?P<S>\d{2})(?:\.\d+)?)?)?$"
)


@dataclass
class DateParseResult:
    value: Optional[datetime]
    error: Optional[str] = None  # set when the cell is non-empty but unparseable

    @property
    def is_empty(self) -> bool:
        return self.value is None and self.error is None


class LongChauDateParser:
    """Never raises: returns ``DateParseResult`` so one bad row can't crash an import.

    Accepts:
      * ``DD/MM/YYYY`` (LongChâu format; also ``-`` or ``.`` separators, optional time)
      * ISO ``YYYY-MM-DD[THH:MM[:SS[.fff]]]`` (Spreadsheet XML DateTime cells)
      * native ``datetime`` / ``date`` (xlsx typed cells)
      * Excel serial numbers (int/float)
    """

    def parse(self, raw: Any) -> DateParseResult:
        if raw is None:
            return DateParseResult(None)
        if isinstance(raw, bool):
            return DateParseResult(None, f"Giá trị ngày không hợp lệ: {raw!r}")
        if isinstance(raw, datetime):
            return DateParseResult(raw)
        if isinstance(raw, date):
            return DateParseResult(datetime(raw.year, raw.month, raw.day))
        if isinstance(raw, (int, float)):
            return self._from_excel_serial(raw)

        text = str(raw).strip()
        if not text:
            return DateParseResult(None)

        for pattern in (_DMY, _ISO):
            m = pattern.match(text)
            if m:
                try:
                    return DateParseResult(
                        datetime(
                            int(m.group("y")), int(m.group("m")), int(m.group("d")),
                            int(m.group("H") or 0), int(m.group("M") or 0), int(m.group("S") or 0),
                        )
                    )
                except ValueError:
                    return DateParseResult(None, f"Ngày không tồn tại: '{text}' (định dạng DD/MM/YYYY)")
        return DateParseResult(None, f"Sai định dạng ngày: '{text}' (cần DD/MM/YYYY)")

    @staticmethod
    def _from_excel_serial(num: float) -> DateParseResult:
        # 1 = 1900-01-01 ... 2958465 = 9999-12-31
        if not (1 <= num <= 2958465):
            return DateParseResult(None, f"Số ngày Excel không hợp lệ: {num}")
        return DateParseResult(_EXCEL_EPOCH + timedelta(days=float(num)))
