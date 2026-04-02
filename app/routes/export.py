from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.services.exporter import export_json, export_markdown
from app.services.session_store import SessionStore


def build_router(store: SessionStore) -> APIRouter:
    router = APIRouter(tags=["export"])

    @router.get("/export/{session_id}")
    async def export_result(session_id: str, format: str = Query(default="json")) -> PlainTextResponse:
        session = store.get(session_id)
        if not session or not session.result:
            raise HTTPException(status_code=404, detail="Extraction result not found")

        if format == "json":
            body = export_json(session.result)
            media_type = "application/json"
            filename = f"{session_id}.json"
        elif format == "markdown":
            body = export_markdown(session.result)
            media_type = "text/markdown"
            filename = f"{session_id}.md"
        else:
            raise HTTPException(status_code=422, detail="format must be json or markdown")

        return PlainTextResponse(
            body,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return router
