from __future__ import annotations

from datetime import datetime, timezone

from app.config import Settings
from app.models.comment import ExtractRequest, ExtractionResult
from app.services.annotator import CommentAnnotator
from app.services.llm_client import LLMClientError, NvidiaLLMClient
from app.services.media_parser import MediaParser
from app.services.scraper import XScraper
from app.services.session_store import SessionStore


class ExtractionManager:
    def __init__(self, settings: Settings, store: SessionStore) -> None:
        self.settings = settings
        self.store = store
        self.scraper = XScraper(settings)
        self.media_parser = MediaParser()
        self.annotator = CommentAnnotator(NvidiaLLMClient(settings))

    async def process_request(self, session_id: str, request: ExtractRequest) -> None:
        try:
            async def on_progress(
                *,
                status: str | None = None,
                progress: int | None = None,
                total_comments: int | None = None,
            ) -> None:
                self.store.update_status(
                    session_id,
                    status=status,
                    progress=progress,
                    total_comments=total_comments,
                )

            post, comments = await self.scraper.extract_post_and_comments(
                request.url,
                max_comments=request.max_comments,
                include_replies=request.include_replies,
                progress_callback=on_progress,
            )

            for index, comment in enumerate(comments, start=1):
                normalized_resources = await self.media_parser.normalize_resources(comment.resources)
                comments[index - 1] = comment.model_copy(update={"index": index, "resources": normalized_resources})

            total = len(comments)
            self.store.update_status(session_id, status="scraping", progress=70, total_comments=total)

            if request.llm_annotate and self.settings.llm_enabled:
                self.store.update_status(session_id, status="annotating", progress=75, total_comments=total)
                try:
                    comments = await self.annotator.annotate_comments(comments)
                except LLMClientError as exc:
                    self.store.update_status(session_id, status="annotating", error=str(exc), progress=85)

            result = ExtractionResult(
                session_id=session_id,
                source_url=request.url,
                post_author=post["author"],
                post_text=post["text"],
                post_timestamp=post["timestamp"],
                total_comments=len(comments),
                extracted_at=datetime.now(timezone.utc),
                comments=comments,
            )
            self.store.set_result(session_id, result)
        except ValueError as exc:
            self.store.update_status(session_id, status="error", progress=100, error=str(exc))
        except Exception as exc:
            self.store.update_status(session_id, status="error", progress=100, error=str(exc))
