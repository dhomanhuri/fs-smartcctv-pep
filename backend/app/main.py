from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.ai.manager import ai_engine_manager
from app.api.v1.auth import router as auth_router
from app.api.v1.cameras import router as camera_router
from app.api.v1.cases import router as cases_router
from app.api.v1.notes import router as notes_router
from app.api.v1.reports import router as reports_router
from app.api.v1.violations import router as violations_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager: Mulai AI engine saat startup, hentikan saat shutdown."""
    # Startup
    snapshot_dir = Path(settings.snapshot_dir)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    ai_engine_manager.start_all()
    yield
    # Shutdown
    ai_engine_manager.stop_all()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="REST API Backend + AI Inference Engine untuk Smart CCTV AI (Pertamina EP)",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:8086", "http://127.0.0.1:8086", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files (Snapshots) ──────────────────────────────────────────────────
snapshot_path = Path(settings.snapshot_dir)
snapshot_path.mkdir(parents=True, exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=str(snapshot_path)), name="snapshots")

# ── Routers API v1 ────────────────────────────────────────────────────────────
api_v1 = FastAPI()
api_v1.include_router(auth_router)
api_v1.include_router(camera_router)
api_v1.include_router(violations_router)
api_v1.include_router(cases_router)
api_v1.include_router(notes_router)
api_v1.include_router(reports_router)

app.mount(settings.api_v1_prefix, api_v1)

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok", "app": settings.app_name}
