import pytest
from fastapi.testclient import TestClient
from app.main import app
import httpx
from unittest.mock import patch, AsyncMock

client = TestClient(app)

def test_proxy_offline_returns_503():
    # When Port 18020 is not reachable, GET /api/test/health should return HTTP 503
    with patch("httpx.AsyncClient.request", side_effect=httpx.ConnectError("Connection refused")):
        response = client.get("/api/test/health")
        assert response.status_code == 503
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "error"
        assert "Khong the ket noi den Test Engine Backend" in data["message"]

def test_proxy_mock_success_forwarding():
    # Test that proxy correctly formats request and returns upstream response
    mock_upstream = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json", "x-action-id": "act_123"},
        json={"success": True, "status": "ok", "service": "test-python-backend"}
    )
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_upstream
        response = client.get("/api/test/health", headers={"x-session-id": "sess_abc", "Authorization": "Bearer secret"})
        assert response.status_code == 200
        assert response.json()["service"] == "test-python-backend"
        
        # Verify call arguments
        call_kwargs = mock_req.call_args.kwargs
        assert call_kwargs["url"] == "http://127.0.0.1:18020/health"
        assert call_kwargs["method"] == "GET"
        headers = call_kwargs["headers"]
        # Authorization header should be stripped
        assert "authorization" not in [k.lower() for k in headers.keys()]
        # Custom tracking headers preserved
        assert headers.get("x-session-id") == "sess_abc"

def test_proxy_url_mapping_rules():
    mock_upstream = httpx.Response(status_code=200, json={"success": True})
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_upstream
        
        # 1. /api/test/api/camera/warehouse/status -> target http://127.0.0.1:18020/api/camera/warehouse/status
        client.get("/api/test/api/camera/warehouse/status")
        assert mock_req.call_args.kwargs["url"] == "http://127.0.0.1:18020/api/camera/warehouse/status"
        
        # 2. /api/test/camera/warehouse/status -> normalized to http://127.0.0.1:18020/api/camera/warehouse/status
        client.get("/api/test/camera/warehouse/status")
        assert mock_req.call_args.kwargs["url"] == "http://127.0.0.1:18020/api/camera/warehouse/status"
        
        # 3. Query string preserved: /api/test/api/zalo/status?include_messages=false
        client.get("/api/test/api/zalo/status?include_messages=false")
        assert mock_req.call_args.kwargs["url"] == "http://127.0.0.1:18020/api/zalo/status?include_messages=false"
