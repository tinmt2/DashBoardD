import logging
from typing import Set
import httpx
from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test", tags=["test-proxy"])
TEST_BACKEND_URL = "http://127.0.0.1:18020"

# Sensitive or transport-specific headers that must NOT be forwarded from client to upstream
EXCLUDED_REQUEST_HEADERS: Set[str] = {
    "host",
    "authorization",  # Protect DashBoardD admin JWT token from leakage to Test engine
    "cookie",
}

# Transport-specific headers that must NOT be forwarded from upstream to client
EXCLUDED_RESPONSE_HEADERS: Set[str] = {
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
}


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_to_test_backend(path: str, request: Request) -> Response:
    """
    Reverse proxy forwarding incoming requests under /api/test/*
    directly to the Test Engine Backend running on port 18020.
    
    Path mapping:
    - /api/test/health -> http://127.0.0.1:18020/health
    - /api/test/api/camera/... -> http://127.0.0.1:18020/api/camera/...
    - /api/test/camera/... -> http://127.0.0.1:18020/api/camera/...
    """
    target_path = path.lstrip("/")
    if not target_path.startswith("api/") and target_path != "health":
        target_path = f"api/{target_path}"

    url = f"{TEST_BACKEND_URL}/{target_path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    # Filter client request headers
    forward_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in EXCLUDED_REQUEST_HEADERS
    }

    try:
        # Generous timeout: 300s for camera sync & report export jobs, 5s connect
        timeout = httpx.Timeout(300.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            req_body = await request.body()
            upstream_response = await client.request(
                method=request.method,
                url=url,
                headers=forward_headers,
                content=req_body,
            )

            # Filter upstream response headers
            resp_headers = {
                k: v for k, v in upstream_response.headers.items()
                if k.lower() not in EXCLUDED_RESPONSE_HEADERS
            }

            return Response(
                content=upstream_response.content,
                status_code=upstream_response.status_code,
                headers=resp_headers,
                media_type=upstream_response.headers.get("content-type"),
            )
    except (httpx.ConnectError, httpx.ConnectTimeout):
        logger.warning(f"[TestProxy] Test Backend is unreachable at {url}")
        return Response(
            content=b'{"success":false,"status":"error","message":"Khong the ket noi den Test Engine Backend (Port 18020). Vui long dam bao Test Backend dang chay."}',
            status_code=503,
            media_type="application/json",
        )
    except httpx.TimeoutException:
        logger.error(f"[TestProxy] Timeout while waiting for Test Backend at {url}")
        return Response(
            content=b'{"success":false,"status":"error","message":"Yeu cau den Test Engine Backend bi het thoi gian cho (Timeout)."}',
            status_code=504,
            media_type="application/json",
        )
    except Exception as e:
        logger.error(f"[TestProxy] Unexpected proxy error forwarding to {url}: {e}")
        return Response(
            content=f'{{"success":false,"status":"error","message":"Loi proxy: {str(e)}"}}'.encode("utf-8"),
            status_code=502,
            media_type="application/json",
        )
