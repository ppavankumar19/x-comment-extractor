from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CommentResource(BaseModel):
    type: str
    url: str
    alt_text: str | None = None
    thumbnail_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommentAuthor(BaseModel):
    username: str
    display_name: str
    avatar_url: str | None = None
    verified: bool = False
    followers_count: int | None = None


class LLMAnnotation(BaseModel):
    sentiment: str
    sentiment_score: float
    topics: list[str]
    summary: str
    language: str
    is_spam: bool


class Comment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    index: int
    comment_id: str
    author: CommentAuthor
    text: str
    text_html: str = ""
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    timestamp: datetime | None = None
    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    bookmark_count: int = 0
    resources: list[CommentResource] = Field(default_factory=list)
    replies: list["Comment"] = Field(default_factory=list)
    annotation: LLMAnnotation | None = None


class ExtractionResult(BaseModel):
    session_id: str
    source_url: str
    post_author: CommentAuthor
    post_text: str
    post_timestamp: datetime | None = None
    total_comments: int
    extracted_at: datetime
    comments: list[Comment] = Field(default_factory=list)


class ExtractRequest(BaseModel):
    url: str
    max_comments: int = Field(default=100, ge=1, le=500)
    include_replies: bool = True
    llm_annotate: bool = False
    llm_backend: str = "nvidia"
    export_format: str = "json"


class SessionStatus(BaseModel):
    session_id: str
    status: str = "pending"
    progress: int = 0
    total_comments: int = 0
    error: str | None = None


class ExtractionSession(BaseModel):
    session_id: str
    request: ExtractRequest
    status: SessionStatus
    result: ExtractionResult | None = None
