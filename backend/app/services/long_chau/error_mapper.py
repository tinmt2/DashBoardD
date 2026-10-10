"""
LongChâu error mapping.

Business rule for this phase: ``LOẠI LỖI`` and ``MÔ TẢ LỖI`` are kept
**verbatim**. No abbreviation, renaming, translation, lower-casing, merging or
invented categories. Grouping belongs to the later analytics phase.

The only transformation is trimming leading/trailing whitespace (incl. stray
``\\n`` at the end of a cell), which does not change the content. Inner text,
punctuation and casing are untouched.

This class deliberately does NOT reuse ``FPTShopErrorMapping``, which
normalizes FPT-specific aliases (e.g. "thiếu tt" -> "Thiếu thông tin").
"""
from __future__ import annotations

from typing import Any, Optional


class LongChauErrorMapper:
    @staticmethod
    def _clean(raw: Any) -> Optional[str]:
        if raw is None:
            return None
        text = str(raw).strip()
        return text or None

    def map_error_type(self, raw: Any) -> Optional[str]:
        return self._clean(raw)

    def map_error_description(self, raw: Any) -> Optional[str]:
        return self._clean(raw)

    @staticmethod
    def error_status(error_type: Optional[str]) -> str:
        """Every LongChâu report row is a recorded violation -> ERROR.

        Rows without ``LOẠI LỖI`` are rejected by the validator, so in practice
        committed rows are always ERROR. PENDING is returned defensively.
        """
        return "ERROR" if error_type else "PENDING"
