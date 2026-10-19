"""
Reminder helper utilities.
Provides flexible and robust detection of reminders ("Nhắc nhở") across diverse variations:
- Accented: 'nhắc nhở', 'nhắc', 'nhăc', 'nhác'
- Unaccented: 'nhac nho', 'nhac', 'da nhac'
- English keywords: 'remind', 'reminder'
- Multiple whitespace, punctuation, typos, or decomposed unicode (NFC/NFD)

Explicitly filters out non-reminder notes (such as employee IDs/names like '37749 - Lê Thị Bảo Trâm Em',
observational text like 'NV không chụp toa thuốc', or empty notes).
"""
import re
import unicodedata
from typing import Optional
from sqlalchemy import or_

def get_reminder_filter(column):
    """
    Returns a SQLAlchemy expression to match reminders in SQL queries.
    Matches variations: 'nhắc', 'nhac', 'nhăc', 'nhác', 'remind', etc.
    """
    return or_(
        column.ilike('%nhắc%'),
        column.ilike('%nhac%'),
        column.ilike('%nhăc%'),
        column.ilike('%nhác%'),
        column.ilike('%remind%')
    )

def remove_accents(input_str: str) -> str:
    """Removes diacritics/accents from a Vietnamese string."""
    if not input_str:
        return ""
    nfkd = unicodedata.normalize('NFKD', input_str)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace('đ', 'd').replace('Đ', 'D')

def is_reminder_note(note: Optional[str]) -> bool:
    """
    Checks in Python whether a note string represents a reminder.
    """
    if not note:
        return False
    norm = remove_accents(unicodedata.normalize('NFC', str(note))).lower()
    norm = re.sub(r'\s+', ' ', norm).strip()
    return 'nhac' in norm or 'remind' in norm
