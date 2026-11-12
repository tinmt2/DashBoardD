import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.routes import health, camera_router, ftel_dvr_router, ticket_router, motion_router, settings_router, zalo_router
from app.services.logging_utils import get_logger, session_id_var, action_id_var, job_id_var, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="test-python-backend",
    description="FastAPI adapter for existing Python PyQt5 Backend",
    version="1.0.0"
)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        session_id = request.headers.get("x-session-id")
        action_id = request.headers.get("x-action-id")
        job_id = request.headers.get("x-job-id")
        
        s_tok = session_id_var.set(session_id) if session_id else None
        a_tok = action_id_var.set(action_id) if action_id else None
        j_tok = job_id_var.set(job_id) if job_id else None
        
        start_time = time.time()
        
        logger.debug(
            f"Incoming request {request.method} {request.url.path}",
            extra={
                "event": "API_REQUEST",
                "metadata": {
                    "method": request.method,
                    "path": request.url.path,
                }
            }
        )
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            logger.debug(
                f"Completed request {request.method} {request.url.path}",
                extra={
                    "event": "API_RESPONSE",
                    "metadata": {
                        "status_code": response.status_code,
                        "duration_ms": round(process_time, 2)
                    }
                }
            )
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "event": "API_ERROR",
                    "metadata": {
                        "duration_ms": round(process_time, 2)
                    }
                }
            )
            raise
        finally:
            if s_tok: session_id_var.reset(s_tok)
            if a_tok: action_id_var.reset(a_tok)
            if j_tok: job_id_var.reset(j_tok)

app.add_middleware(LoggingMiddleware)

# Configure CORS for Electron development
# Fast API will bind only to 127.0.0.1:18020
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(camera_router.router)
app.include_router(ftel_dvr_router.router)
app.include_router(ticket_router.router)
app.include_router(motion_router.router)
app.include_router(settings_router.router)
app.include_router(zalo_router.router)

ZALO_TASK = None

@app.on_event("startup")
def startup_event():
    import threading
    from app.services.warehouse_sync import fetch_and_cache_warehouse
    def run_sync():
        fetch_and_cache_warehouse()
    t = threading.Thread(target=run_sync, daemon=True)
    t.start()
    
    # Background worker for Zalo monitoring loop
    import asyncio
    from app.services.zalo_monitor_service import zalo_monitor_service

    # LƯU Ý: Không tự động bật Chrome khi mở app.
    # Chỉ mở Chrome khi người dùng bấm nút [Mở Zalo] hoặc [Bắt đầu giám sát].
    
    async def zalo_loop_worker():
        while True:
            try:
                await zalo_monitor_service.run_loop_step()
            except Exception:
                pass
            await asyncio.sleep(10)
    global ZALO_TASK
    ZALO_TASK = asyncio.create_task(zalo_loop_worker())

@app.on_event("shutdown")
def shutdown_event():
    global ZALO_TASK
    if ZALO_TASK and not ZALO_TASK.done():
        try:
            ZALO_TASK.cancel()
        except Exception:
            pass
    try:
        from app.services import backend_check
        from app.api.routes.camera_router import JOB_STORE as CAM_JOBS
        for jid, jdata in list(CAM_JOBS.items()):
            if jdata.get("status") in ["queued", "running"]:
                backend_check.signal_stop(jid)
    except Exception:
        pass
    try:
        from app.services import backend_check
        from app.api.routes.ftel_dvr_router import FTEL_STATE, JOB_STORE as DVR_JOBS
        backend_check.GLOBAL_STOP = True
        if FTEL_STATE.get("worker") and hasattr(FTEL_STATE["worker"], "stop"):
            FTEL_STATE["worker"].stop()
        for jid, jdata in list(DVR_JOBS.items()):
            if jdata.get("status") in ["queued", "running"]:
                backend_check.signal_stop(jid)
                if jdata.get("worker") and hasattr(jdata["worker"], "stop"):
                    jdata["worker"].stop()
    except Exception:
        pass
    try:
        from app.api.routes.ticket_router import JOB_STORE as TICKET_JOBS
        for jid, jdata in list(TICKET_JOBS.items()):
            if jdata.get("status") in ["queued", "running"]:
                worker = jdata.get("_worker")
                if worker and hasattr(worker, "stop"):
                    worker.stop()
                jdata["_orchestrator_running"] = False
                for w in jdata.get("_workers", []):
                    if hasattr(w, "stop"):
                        w.stop()
    except Exception:
        pass
    try:
        from app.api.routes.ticket_router import GLOBAL_TICKET_DRIVER
        if GLOBAL_TICKET_DRIVER:
            GLOBAL_TICKET_DRIVER.quit()
    except Exception:
        pass
    try:
        from app.services.zalo_web_adapter import zalo_web_adapter
        zalo_web_adapter.close_browser()
    except Exception:
        pass
    try:
        from app.services.browser_manager import cleanup_chrome_sessions
        from app.services.zalo_web_adapter import zalo_web_adapter
        cleanup_chrome_sessions(zalo_web_adapter.profile_dir)
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=18020)
