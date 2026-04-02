# Specification

**Status:** implemented repository snapshot  
**Last Updated:** 2026-04-02

## Architecture

The application is a single FastAPI service with an in-memory session store.

```text
Browser
  -> GET /                    bundled HTML with inline CSS and JS
  -> POST /extract            starts async extraction
  -> GET /status/{id}         polls progress
  -> GET /results/{id}        returns structured result
  -> GET /export/{id}         downloads JSON or Markdown

FastAPI
  -> ExtractionManager
     -> XScraper
     -> MediaParser
     -> CommentAnnotator
```

## Frontend Delivery

- `frontend/index.html` is the source template.
- `app/frontend.py` reads `index.html`, `style.css`, and `app.js`.
- The CSS and JavaScript are inlined into the HTML response.
- The current build does not expose a `/static` route.

## Request Model

```python
class ExtractRequest(BaseModel):
    url: str
    max_comments: int = Field(default=100, ge=1, le=500)
    include_replies: bool = True
    llm_annotate: bool = False
    llm_backend: str = "nvidia"
    export_format: str = "json"
```

Behavioral constraints:

- `url` must be an `x.com` or `twitter.com` status URL.
- `llm_backend` must currently be `"nvidia"`, otherwise the API returns HTTP 422.

## Result Model

The main persisted object is `ExtractionResult` in [app/models/comment.py](/home/pavankumar19/x-comment-extractor/app/models/comment.py).

Top-level fields:

- `session_id`
- `source_url`
- `post_author`
- `post_text`
- `post_timestamp`
- `total_comments`
- `extracted_at`
- `comments`

Each `Comment` includes:

- identity: `index`, `comment_id`
- author: username, display name, avatar, verified flag
- content: `text`, `text_html`, `hashtags`, `mentions`, `emails`, `links`
- metrics: like, retweet, reply, bookmark counts
- media/resources: normalized `CommentResource` entries
- nested `replies`
- optional `annotation`

## Extraction Flow

1. Validate the X status URL.
2. Create an in-memory session with `pending` status.
3. Launch Playwright Chromium.
4. Load the post, dismiss basic popups, and wait for tweet articles.
5. Scroll and expand reply controls until progress stalls or the requested limit is reached.
6. Build the post payload and comment list from DOM-extracted article data.
7. Normalize outbound `t.co` links and deduplicate resources.
8. Optionally annotate top-level comments with the NVIDIA client.
9. Store `ExtractionResult` and mark the session done.

## Implemented Resource Coverage

Current `XScraper` and `MediaParser` behavior supports:

- images
- videos
- GIF-like looping video elements
- outbound links, including `t.co` expansion

Not implemented in the current code:

- OG card enrichment
- poll extraction
- quote-tweet parsing
- persistent database storage
- non-NVIDIA annotation backends

## Session Lifecycle

Session state is stored in memory through `SessionStore` and surfaced through `SessionStatus`.

Observed status values used by the app:

- `pending`
- `scraping`
- `annotating`
- `done`
- `error`

## Export

- `format=json` returns `ExtractionResult.model_dump_json(indent=2)`
- `format=markdown` returns a nested Markdown report with post metadata, comments, replies, resources, and optional annotations

## Verification

The repository includes unit tests for:

- X URL validation and count parsing
- NVIDIA response parsing
- frontend bundling behavior
