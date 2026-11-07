import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_inside_creds():
    response = client.get("/api/inside/creds")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "username" in data
    assert "has_password" in data

def test_save_inside_creds():
    response = client.post("/api/inside/creds", json={"username": "tinmt2", "password": "Trongtinn96@"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["username"] == "tinmt2"
