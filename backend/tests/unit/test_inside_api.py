import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import get_admin_config

client = TestClient(app)

@pytest.fixture
def admin_headers():
    import time
    from unittest.mock import patch
    token = "test_valid_admin_token_12345"
    orig_get_cfg = get_admin_config()
    mock_cfg = dict(orig_get_cfg)
    mock_cfg["active_tokens"] = [{"token": token, "created_at": time.time()}]
    with patch("app.core.auth.get_admin_config", return_value=mock_cfg):
        yield {"Authorization": f"Bearer {token}"}

def test_get_inside_creds_unauthorized():
    # Request without token must be rejected with HTTP 401
    resp_no_token = client.get("/api/inside/creds")
    assert resp_no_token.status_code == 401
    assert resp_no_token.json()["detail"] == "Chưa có token xác thực!"

    # Request with invalid token must be rejected with HTTP 401
    resp_invalid = client.get("/api/inside/creds", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert resp_invalid.status_code == 401
    assert resp_invalid.json()["detail"] == "Phiên đăng nhập Admin đã hết hạn hoặc không hợp lệ!"

def test_get_inside_creds(admin_headers):
    response = client.get("/api/inside/creds", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "username" in data
    assert "has_password" in data

def test_save_inside_creds_unauthorized():
    payload = {"username": "tinmt2", "password": "Trongtinn96@"}
    # Request without token must be rejected with HTTP 401
    resp_no_token = client.post("/api/inside/creds", json=payload)
    assert resp_no_token.status_code == 401
    assert resp_no_token.json()["detail"] == "Chưa có token xác thực!"

    # Request with invalid token must be rejected with HTTP 401
    resp_invalid = client.post("/api/inside/creds", json=payload, headers={"Authorization": "Bearer invalid_token_xyz"})
    assert resp_invalid.status_code == 401
    assert resp_invalid.json()["detail"] == "Phiên đăng nhập Admin đã hết hạn hoặc không hợp lệ!"

def test_save_inside_creds(admin_headers):
    response = client.post("/api/inside/creds", json={"username": "tinmt2", "password": "Trongtinn96@"}, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["username"] == "tinmt2"
