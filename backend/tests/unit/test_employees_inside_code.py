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
    assert "note" in vien

def test_employee_note_update_persistence():
    # Update note for VienND2
    patch_res = client.patch("/api/employees/VienND2/note", json={"note": "Test Note For Persistence"})
    assert patch_res.status_code == 200
    res_data = patch_res.json()
    assert res_data["success"] is True
    assert res_data["note"] == "Test Note For Persistence"

    # Verify GET returns updated note
    get_res = client.get("/api/employees")
    assert get_res.status_code == 200
    all_emps = get_res.json()
    vien = next((e for e in all_emps if e["id"] == "VienND2"), None)
    assert vien is not None
    assert vien["note"] == "Test Note For Persistence"

    # Clean up test note
    clean_res = client.patch("/api/employees/VienND2/note", json={"note": ""})
    assert clean_res.status_code == 200


def test_employee_inside_chain_update_persistence():
    # Update insideChain for VienND2
    patch_res = client.patch("/api/employees/VienND2/inside-chain", json={"insideChain": "Vaccine"})
    assert patch_res.status_code == 200
    res_data = patch_res.json()
    assert res_data["success"] is True
    assert res_data["insideChain"] == "Vaccine"

    # Verify GET returns updated insideChain
    get_res = client.get("/api/employees")
    assert get_res.status_code == 200
    all_emps = get_res.json()
    vien = next((e for e in all_emps if e["id"] == "VienND2"), None)
    assert vien is not None
    assert vien["insideChain"] == "Vaccine"

    # Revert back to FPT Shop
    revert_res = client.patch("/api/employees/VienND2/inside-chain", json={"insideChain": "FPT Shop"})
    assert revert_res.status_code == 200
