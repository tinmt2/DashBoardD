import pytest
from app.core.reminder import is_reminder_note, remove_accents

def test_is_reminder_note_variations():
    # Standard variations
    assert is_reminder_note("Nhắc nhở") is True
    assert is_reminder_note("nhắc nhở") is True
    assert is_reminder_note("NHẮC NHỞ") is True
    assert is_reminder_note("Nhắc nhở do khắc phục trong thời gian quy định") is True
    assert is_reminder_note("Nhắc nhở do khắc phục trong thời gian quy định.") is True
    assert is_reminder_note(".Nhắc nhở do khắc phục trong thời gian quy định ..") is True

    # Spacing and typos
    assert is_reminder_note("Nhắc  nhở") is True
    assert is_reminder_note("Nhắc   nhở") is True
    assert is_reminder_note("Nhắc nhở do khăc phục trong thời gian quy định") is True
    assert is_reminder_note("Nhắc nhở do khắc phục trong thời gian quy đinh") is True

    # Decomposed unicode (NFD)
    import unicodedata
    nfd_note = unicodedata.normalize('NFD', "Nhắc nhở")
    assert is_reminder_note(nfd_note) is True

    # Unaccented
    assert is_reminder_note("nhac nho") is True
    assert is_reminder_note("Nhac nho do khac phuc") is True
    assert is_reminder_note("da nhac nho nhan vien") is True

    # English keyword
    assert is_reminder_note("Reminder sent") is True
    assert is_reminder_note("remind employee") is True

def test_is_reminder_note_exclusions():
    # Employee IDs and names should NOT be reminders
    assert is_reminder_note("37749 - Lê Thị Bảo Trâm Em") is False
    assert is_reminder_note("107676--Trần Tuấn Duy") is False
    assert is_reminder_note("26542--Lữ Trọng Thành") is False
    assert is_reminder_note("111376-Nguyễn Bá Toàn") is False

    # Observational notes without reminder keywords should NOT be reminders
    assert is_reminder_note("NV không chụp và up hình toa thuốc") is False
    assert is_reminder_note("Không ghi nhận") is False
    assert is_reminder_note("Điều dưỡng tiêm 74022-Phạm Thị Thắm") is False
    assert is_reminder_note("Khu vực cảnh quan shop chưa gọn gàng") is False
    assert is_reminder_note("test") is False
    assert is_reminder_note("") is False
    assert is_reminder_note(None) is False
