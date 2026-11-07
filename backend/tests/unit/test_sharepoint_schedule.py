from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_schedule_links_and_seed():
    response = client.get("/api/employees/schedule-links")
    assert response.status_code == 200
    links = response.json()
    assert isinstance(links, list)
    assert len(links) >= 1
    # Check default seeded month 2026-11
    nov_link = next((l for l in links if l["month"] == "2026-11"), None)
    assert nov_link is not None
    assert "LLV T11 2026.xlsx" in nov_link["fileName"]

def test_upsert_schedule_link():
    payload = {
        "month": "2026-12",
        "sharepointUrl": "https://fptsoftware362.sharepoint.com/:x:/r/sites/FRT.ICT.HO/VHShop/GSCMR/_layouts/15/doc2.aspx?file=1.%20LLV%20T12%202026.xlsx",
        "title": "Lịch làm việc Tháng 12/2026",
        "note": "Test month 12"
    }
    res = client.post("/api/employees/schedule-links", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["month"] == "2026-12"
    assert data["fileName"] == "1. LLV T12 2026.xlsx"

    # Cleanup test month 12
    del_res = client.delete("/api/employees/schedule-links/2026-12")
    assert del_res.status_code == 200

def test_get_shift_matrix():
    response = client.get("/api/employees/schedule/matrix?month=2026-11")
    assert response.status_code == 200
    data = response.json()
    assert data["month"] == "2026-11"
    assert len(data["dates"]) > 0
    assert len(data["employees"]) > 0

def test_sharepoint_auth_status():
    response = client.get("/api/employees/sharepoint/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert "authenticated" in data
    assert "status" in data
    assert data["profileName"] == "sharepoint-profile"
