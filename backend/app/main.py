from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.fpt_shop.browser_session import FPTBrowserSession
from app.services.scheduler.auto_sync_service import AutoSyncService

@asynccontextmanager
async def lifespan(app: FastAPI):
    auto_sync = AutoSyncService.get_instance()
    auto_sync.start()
    yield
    # Cleanup on shutdown
    auto_sync.stop()
    session = FPTBrowserSession.get_instance()
    session.stop()

from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging
from app.core.database import engine, Base
import app.models.ticket
import app.models.import_job
import app.models.long_chau
import app.models.notification
import app.models.employee

Base.metadata.create_all(bind=engine)

setup_logging()

app = FastAPI(title="OpsMonitor FPT Shop API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import health, fpt_shop, long_chau, long_chau_dashboard, vaccine, vaccine_dashboard, notifications, admin, employees, auto_sync, inside

app.include_router(health.router, prefix="/api")
app.include_router(inside.router, prefix="/api")
app.include_router(admin.router, prefix="/api/admin")
app.include_router(employees.router, prefix="/api/employees")
app.include_router(fpt_shop.router, prefix="/api/fpt-shop")
app.include_router(long_chau.router, prefix="/api/long-chau")
app.include_router(long_chau_dashboard.router, prefix="/api")
app.include_router(vaccine.router, prefix="/api/vaccine")
app.include_router(vaccine_dashboard.router, prefix="/api")
app.include_router(notifications.router, prefix="/api/notifications")
app.include_router(auto_sync.router, prefix="/api/auto-sync")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dashboard-app", "dist"))

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/favicon.ico")
    async def get_favicon_ico():
        ico_path = os.path.join(frontend_dist, "favicon.ico")
        if os.path.isfile(ico_path):
            return FileResponse(ico_path, media_type="image/x-icon", headers={"Cache-Control": "no-cache, must-revalidate"})
        return FileResponse(os.path.join(frontend_dist, "favicon.svg"), media_type="image/svg+xml")

    @app.get("/favicon.svg")
    async def get_favicon_svg():
        return FileResponse(os.path.join(frontend_dist, "favicon.svg"), media_type="image/svg+xml", headers={"Cache-Control": "no-cache, must-revalidate"})

    @app.get("/favicon.png")
    async def get_favicon_png():
        return FileResponse(os.path.join(frontend_dist, "favicon.png"), media_type="image/png", headers={"Cache-Control": "no-cache, must-revalidate"})

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        from fastapi import HTTPException
        # 1. API routes must 404 if not matched by routers
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        
        # 2. Block common internet crawler / vulnerability scanning probes
        clean_path = full_path.lower().strip()
        blocked_exts = (".env", ".php", ".sql", ".bak", ".old", ".save", ".swp", ".dist", ".yml", ".yaml", ".ini", ".conf", ".config", ".xml", ".db", ".sqlite", ".git", ".sh", ".bash", ".log", ".tar", ".gz", ".zip", ".rar", ".7z", ".asp", ".aspx", ".jsp", ".action", ".do", ".cgi")
        blocked_prefixes = ("wp-", "wordpress", "phpmyadmin", "actuator", "cgi-bin", "autodiscover", ".git", ".env", ".aws", ".config", ".svn", "solr", "telescope")
        
        if any(clean_path.startswith(p) or f"/{p}" in clean_path for p in blocked_prefixes) or any(clean_path.endswith(ext) for ext in blocked_exts):
            raise HTTPException(status_code=404, detail="Not found")

        # 3. Safe static file lookup with path-traversal prevention
        file_path = os.path.abspath(os.path.join(frontend_dist, full_path))
        if os.path.commonpath([file_path, frontend_dist]) == frontend_dist and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # 4. If request has a file extension (e.g. non-existent file) but not found on disk, return 404
        basename = os.path.basename(clean_path)
        if "." in basename and not basename.startswith("."):
            raise HTTPException(status_code=404, detail="File not found")

        # 5. Clean SPA client-side routes (e.g. /admin, /dashboard, /login) -> serve index.html
        return FileResponse(
            os.path.join(frontend_dist, "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
else:
    @app.get("/")
    def read_root():
        return {"message": "OpsMonitor API is running (Frontend dist not found)"}
