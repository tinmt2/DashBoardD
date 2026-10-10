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
from app.api import health, fpt_shop, long_chau
from app.core.logging import setup_logging
from app.core.database import engine, Base
import app.models.ticket
import app.models.import_job
import app.models.long_chau

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

from app.api import health, fpt_shop, long_chau, long_chau_dashboard, vaccine, vaccine_dashboard

app.include_router(health.router, prefix="/api")
app.include_router(fpt_shop.router, prefix="/api/fpt-shop")
app.include_router(long_chau.router, prefix="/api/long-chau")
app.include_router(long_chau_dashboard.router, prefix="/api")
app.include_router(vaccine.router, prefix="/api/vaccine")
app.include_router(vaccine_dashboard.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "OpsMonitor API is running"}
