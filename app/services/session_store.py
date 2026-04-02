from __future__ import annotations

from threading import Lock

from app.models.comment import ExtractRequest, ExtractionResult, ExtractionSession, SessionStatus


class SessionStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, ExtractionSession] = {}

    def create(self, session_id: str, request: ExtractRequest) -> ExtractionSession:
        session = ExtractionSession(
            session_id=session_id,
            request=request,
            status=SessionStatus(session_id=session_id),
        )
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> ExtractionSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def update_status(
        self,
        session_id: str,
        *,
        status: str | None = None,
        progress: int | None = None,
        total_comments: int | None = None,
        error: str | None = None,
    ) -> ExtractionSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            if status is not None:
                session.status.status = status
            if progress is not None:
                session.status.progress = progress
            if total_comments is not None:
                session.status.total_comments = total_comments
            if error is not None:
                session.status.error = error
            return session

    def set_result(self, session_id: str, result: ExtractionResult) -> ExtractionSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            session.result = result
            session.status.total_comments = result.total_comments
            session.status.progress = 100
            session.status.status = "done"
            return session
