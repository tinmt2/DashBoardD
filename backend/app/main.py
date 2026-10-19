from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.fpt_shop.browser_session import FPTBrowserSession

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Cleanup on shutdown
    session = FPTBrowserSession.get_instance()
    session.stop()

from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging
from app.core.database import engine, Base
import app.models.ticket
import app.models.import_job
import app.models.long_chau
import app.models.notification

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

from app.api import health, fpt_shop, long_chau, long_chau_dashboard, vaccine, vaccine_dashboard, notifications

app.include_router(health.router, prefix="/api")
app.include_router(fpt_shop.router, prefix="/api/fpt-shop")
app.include_router(long_chau.router, prefix="/api/long-chau")
app.include_router(long_chau_dashboard.router, prefix="/api")
app.include_router(vaccine.router, prefix="/api/vaccine")
app.include_router(vaccine_dashboard.router, prefix="/api")
app.include_router(notifications.router, prefix="/api/notifications")

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
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API route not found")
        
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(
            os.path.join(frontend_dist, "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
else:
    @app.get("/")
    def read_root():
        return {"message": "OpsMonitor API is running (Frontend dist not found)"}
