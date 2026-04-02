from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.frontend import render_frontend
from app.routes.export import build_router as build_export_router
from app.routes.extract import build_router as build_extract_router
from app.routes.status import build_router as build_status_router
from app.services.extraction import ExtractionManager
from app.services.session_store import SessionStore

settings = get_settings()
store = SessionStore()
manager = ExtractionManager(settings, store)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(build_extract_router(store, manager))
app.include_router(build_status_router(store))
app.include_router(build_export_router(store))


@app.get("/", include_in_schema=False)
async def index() -> HTMLResponse:
    return HTMLResponse(render_frontend(FRONTEND_DIR))


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)
