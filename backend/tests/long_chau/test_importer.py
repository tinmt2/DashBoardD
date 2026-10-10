import os
import pytest
from app.services.long_chau.service import LongChauImportService
from sqlalchemy.orm import Session

@pytest.fixture
def test_export_file():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "fixtures", "export.xls")

def test_importer_preview(test_export_file, db_session: Session):
    importer = LongChauImportService(db_session)
    
    with open(test_export_file, "rb") as f:
        file_bytes = f.read()
        
    result = importer.preview("export.xls", file_bytes)
    assert result.get("success") is True, f"Preview failed: {result}"
    
    assert result["totalRows"] > 0
    assert result["sheetName"] == "SHEET 1"
    assert len(result["previewRows"]) > 0

    unique_ids = set()
    for row in result["previewRows"]:
        unique_ids.add(row["ticketId"])
    
    assert len(unique_ids) > 0

def test_importer_commit(test_export_file, db_session: Session):
    importer = LongChauImportService(db_session)
    
    with open(test_export_file, "rb") as f:
        file_bytes = f.read()
        
    preview = importer.preview("export.xls", file_bytes)
    assert preview.get("success") is True
    assert preview["validRows"] > 0
    import_id = preview["importId"]

    commit_result = importer.commit(import_id)
    assert commit_result.get("success") is True
    assert commit_result["summary"]["inserted"] > 0
    
    # Second commit should fail because status is not PREVIEW_READY
    commit_result2 = importer.commit(import_id)
    assert commit_result2.get("success") is False
