import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

@pytest.fixture
def notif_client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    prev_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    
    yield client

    if prev_override is not None:
        app.dependency_overrides[get_db] = prev_override
    else:
        app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)

def test_notification_lifecycle(notif_client):
    client = notif_client

    # 1. Ban đầu danh sách rỗng
    res = client.get("/api/notifications")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total"] == 0
    assert data["unread_count"] == 0
    assert data["items"] == []

    # 2. Tạo thông báo đồng bộ tất cả 3 chuỗi
    payload = {
        "title": "Đồng bộ tất cả 3 chuỗi hoàn tất",
        "status": "SUCCESS",
        "sync_type": "SYNC_ALL",
        "start_date": "2026-10-01",
        "end_date": "2026-10-17",
        "total_new_errors": 18,
        "total_scanned": 195,
        "total_duplicates": 177,
        "chain_details": [
            {
                "chain": "FPT Shop",
                "status": "SUCCESS",
                "new_records": 10,
                "total_rows": 120,
                "duplicate_records": 110,
                "error_message": None
            },
            {
                "chain": "Long Châu",
                "status": "SUCCESS",
                "new_records": 5,
                "total_rows": 45,
                "duplicate_records": 40,
                "error_message": None
            },
            {
                "chain": "Vaccine",
                "status": "SUCCESS",
                "new_records": 3,
                "total_rows": 30,
                "duplicate_records": 27,
                "error_message": None
            }
        ]
    }
    create_res = client.post("/api/notifications", json=payload)
    assert create_res.status_code == 200
    created = create_res.json()["item"]
    assert created["title"] == payload["title"]
    assert created["total_new_errors"] == 18
    assert len(created["chain_details"]) == 3
    assert created["chain_details"][0]["new_records"] == 10
    assert created["chain_details"][1]["new_records"] == 5
    assert created["chain_details"][2]["new_records"] == 3
    assert created["is_read"] is False
    notif_id = created["id"]

    # 3. Tạo thông báo thứ 2: Đồng bộ Vaccine thất bại
    payload_failed = {
        "title": "Đồng bộ Vaccine thất bại",
        "status": "FAILED",
        "sync_type": "VACCINE",
        "start_date": "2026-10-10",
        "end_date": "2026-10-17",
        "total_new_errors": 0,
        "total_scanned": 0,
        "total_duplicates": 0,
        "chain_details": [
            {
                "chain": "Vaccine",
                "status": "FAILED",
                "new_records": 0,
                "total_rows": 0,
                "duplicate_records": 0,
                "error_message": "Phiên đăng nhập Vaccine đã hết hạn."
            }
        ],
        "error_message": "Phiên đăng nhập Vaccine đã hết hạn."
    }
    client.post("/api/notifications", json=payload_failed)

    # 4. Kiểm tra danh sách & unread_count
    list_res = client.get("/api/notifications")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 2
    assert list_data["unread_count"] == 2

    # 5. Đánh dấu đọc thông báo thứ 1
    read_res = client.patch(f"/api/notifications/{notif_id}/read")
    assert read_res.status_code == 200
    assert read_res.json()["item"]["is_read"] is True

    # Kiểm tra unread giảm còn 1
    unread_res = client.get("/api/notifications?unread_only=true")
    assert len(unread_res.json()["items"]) == 1
    assert unread_res.json()["unread_count"] == 1

    # 6. Đánh dấu tất cả đã đọc
    mark_all = client.post("/api/notifications/mark-all-read")
    assert mark_all.status_code == 200
    assert mark_all.json()["updated"] == 1

    list_after_read = client.get("/api/notifications")
    assert list_after_read.json()["unread_count"] == 0

    # 7. Xoá thông báo đơn lẻ
    del_res = client.delete(f"/api/notifications/{notif_id}")
    assert del_res.status_code == 200

    list_after_del = client.get("/api/notifications")
    assert list_after_del.json()["total"] == 1

    # 8. Xoá tất cả thông báo
    clear_res = client.delete("/api/notifications")
    assert clear_res.status_code == 200
    assert clear_res.json()["deleted"] == 1

    final_res = client.get("/api/notifications")
    assert final_res.json()["total"] == 0
