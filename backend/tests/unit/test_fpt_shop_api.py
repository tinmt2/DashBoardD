import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pandas as pd
import io

from app.main import app
from app.core.database import Base, get_db
from app.models.import_job import ImportJob
from app.models.ticket import Ticket

# Setup in-memory sqlite
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def create_dummy_excel():
    df = pd.DataFrame({
        "Ticket ID": ["T001", "T002"],
        "Tên nhân viên": ["Emp A", "Emp B"],
        "Loại lỗi": ["Thiếu thông tin", ""]
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def test_import_preview_and_commit():
    # 1. Preview
    file_bytes = create_dummy_excel()
    response = client.post(
        "/api/fpt-shop/import/preview",
        files={"file": ("test.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "PREVIEW_READY"
    assert data["summary"]["total_rows"] == 2
    
    import_id = data["import_id"]
    
    # 2. History check
    hist_resp = client.get("/api/fpt-shop/import/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert len(hist_data["history"]) == 1
    assert hist_data["history"][0]["import_id"] == import_id
    
    # 3. Commit
    commit_resp = client.post("/api/fpt-shop/import/commit", json={"import_id": import_id})
    assert commit_resp.status_code == 200
    commit_data = commit_resp.json()
    assert commit_data["success"] is True
    assert commit_data["summary"]["new"] == 2
    assert commit_data["summary"]["duplicate"] == 0
    
    # 4. Idempotency test
    commit_resp_2 = client.post("/api/fpt-shop/import/commit", json={"import_id": import_id})
    assert commit_resp_2.status_code == 400 # Cannot commit COMPLETED job
    
    # 5. Duplicate test with a new job containing same data
    file_bytes_2 = create_dummy_excel()
    resp2 = client.post(
        "/api/fpt-shop/import/preview",
        files={"file": ("test2.xlsx", file_bytes_2, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    import_id_2 = resp2.json()["import_id"]
    
    commit_resp_3 = client.post("/api/fpt-shop/import/commit", json={"import_id": import_id_2})
    assert commit_resp_3.status_code == 200
    commit_data_3 = commit_resp_3.json()
    assert commit_data_3["success"] is True
    assert commit_data_3["summary"]["new"] == 0
    assert commit_data_3["summary"]["duplicate"] == 2
