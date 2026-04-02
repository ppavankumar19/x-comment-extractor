from __future__ import annotations

from app.models.comment import Comment
from app.services.llm_client import NvidiaLLMClient


class CommentAnnotator:
    def __init__(self, llm_client: NvidiaLLMClient) -> None:
        self.llm_client = llm_client

    async def annotate_comments(self, comments: list[Comment]) -> list[Comment]:
        annotated: list[Comment] = []
        for comment in comments:
            annotation = await self.llm_client.annotate(comment.text)
            annotated.append(comment.model_copy(update={"annotation": annotation}))
        return annotated
