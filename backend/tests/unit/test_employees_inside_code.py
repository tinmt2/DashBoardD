import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_employees_has_inside_code():
    res = client.get("/api/employees")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 38
    # Check that insideCode is present in every employee
    has_inside = any(e.get("insideCode") for e in data)
    assert has_inside is True
    
    # Check specific employee
    vien = next((e for e in data if e["id"] == "VienND2"), None)
    assert vien is not None
    assert vien["insideCode"] == "51765"
    assert vien["name"] == "Ngô Đức Viện"
    assert vien["chain"] == "FPT Shop"
