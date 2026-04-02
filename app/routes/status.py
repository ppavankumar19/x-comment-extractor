from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.session_store import SessionStore


def build_router(store: SessionStore) -> APIRouter:
    router = APIRouter(tags=["status"])

    @router.get("/status/{session_id}")
    async def get_status(session_id: str) -> dict:
        session = store.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.status.model_dump()

    @router.get("/results/{session_id}")
    async def get_results(session_id: str) -> dict:
        session = store.get(session_id)
        if not session or not session.result:
            raise HTTPException(status_code=404, detail="Extraction result not found")
        return session.result.model_dump(mode="json")

    return router
