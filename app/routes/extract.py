from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.models.comment import ExtractRequest
from app.services.extraction import ExtractionManager
from app.services.scraper import validate_x_url
from app.services.session_store import SessionStore

router = APIRouter(tags=["extract"])


def build_router(store: SessionStore, manager: ExtractionManager) -> APIRouter:
    @router.post("/extract")
    async def start_extraction(request: ExtractRequest) -> dict[str, str]:
        if request.llm_backend.lower() != "nvidia":
            raise HTTPException(status_code=422, detail="Only the NVIDIA backend is implemented")
        if not validate_x_url(request.url):
            raise HTTPException(status_code=422, detail="Please provide a valid X post URL")

        session_id = uuid4().hex
        store.create(session_id, request)
        asyncio.create_task(manager.process_request(session_id, request))
        return {
            "session_id": session_id,
            "status": "processing",
            "message": f"Extraction started. Poll /status/{session_id} for updates.",
        }

    return router
