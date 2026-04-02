# 📐 SPECIFICATION.md — X Post Comment Extractor Agent

**Version:** 1.0.0  
**Status:** Draft  
**Last Updated:** 2025  

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Browser)                           │
│                    Web UI — index.html                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP (REST)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ /extract     │  │ /status      │  │ /export              │  │
│  │ POST         │  │ GET          │  │ GET ?format=json/md  │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────────┘  │
│         │                                                        │
│  ┌──────▼──────────────────────────────────────────────────┐    │
│  │                    Service Layer                         │    │
│  │  ┌────────────┐  ┌──────────────┐  ┌────────────────┐  │    │
│  │  │  Scraper   │  │ MediaParser  │  │  LLM Annotator │  │    │
│  │  │ Playwright │  │ (img/vid/url)│  │ Ollama/NVIDIA  │  │    │
│  │  └────────────┘  └──────────────┘  └────────────────┘  │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
            │                           │
            ▼                           ▼
   ┌─────────────────┐       ┌─────────────────────┐
   │  X (Twitter)    │       │  LLM Backend        │
   │  Public Pages   │       │  Ollama (local)     │
   │  (Playwright)   │       │  NVIDIA NIM (cloud) │
   └─────────────────┘       └─────────────────────┘
```

---

## 2. Data Models

### 2.1 Input

```python
class ExtractRequest(BaseModel):
    url: str                        # X post URL
    max_comments: int = 100         # Max top-level comments to fetch
    include_replies: bool = True    # Fetch nested reply threads
    llm_annotate: bool = False      # Optional NVIDIA annotation
    llm_backend: str = "nvidia"     # NVIDIA only in current build
    export_format: str = "json"     # "json" or "markdown"
```

### 2.2 Comment Object

```python
class CommentResource(BaseModel):
    type: str                       # "image" | "video" | "gif" | "link" | "quote_tweet" | "poll"
    url: str                        # Direct URL to resource
    alt_text: Optional[str]         # Alt text for images
    thumbnail_url: Optional[str]    # Preview thumbnail for video/link
    metadata: Dict[str, Any]        # Extra info (duration, width, height, og:title, etc.)

class CommentAuthor(BaseModel):
    username: str                   # @handle
    display_name: str               # Full display name
    avatar_url: Optional[str]       # Profile picture URL
    verified: bool                  # Blue/gold checkmark status
    followers_count: Optional[int]

class LLMAnnotation(BaseModel):
    sentiment: str                  # "positive" | "negative" | "neutral" | "mixed"
    sentiment_score: float          # 0.0 – 1.0
    topics: List[str]               # Extracted topic tags
    summary: str                    # 1-sentence summary
    language: str                   # Detected language (ISO 639-1)
    is_spam: bool                   # Spam detection flag

class Comment(BaseModel):
    index: int                      # Sequential number (1, 2, 3…)
    comment_id: str                 # X internal tweet ID
    author: CommentAuthor
    text: str                       # Raw comment text
    text_html: str                  # HTML-rendered version with links
    hashtags: List[str]             # Extracted #hashtags
    mentions: List[str]             # Extracted @mentions
    timestamp: datetime             # Posted at
    like_count: int
    retweet_count: int
    reply_count: int
    bookmark_count: int
    resources: List[CommentResource]  # All media and links
    replies: List["Comment"]        # Nested reply thread
    annotation: Optional[LLMAnnotation]

class ExtractionResult(BaseModel):
    session_id: str
    source_url: str
    post_author: CommentAuthor
    post_text: str
    post_timestamp: datetime
    total_comments: int
    extracted_at: datetime
    comments: List[Comment]
```

---

## 3. API Endpoints

### 3.1 `POST /extract`

**Request:**
```json
{
  "url": "https://x.com/user/status/12345",
  "max_comments": 50,
  "include_replies": true,
  "llm_annotate": true,
  "llm_backend": "nvidia"
}
```

**Response:**
```json
{
  "session_id": "abc123",
  "status": "processing",
  "message": "Extraction started. Poll /status/{session_id} for updates."
}
```

**Note:** Extraction runs as a background task. Results are retrieved via `/status` and `/results`.

---

### 3.2 `GET /status/{session_id}`

```json
{
  "session_id": "abc123",
  "status": "done",           // "pending" | "scraping" | "annotating" | "done" | "error"
  "progress": 100,
  "total_comments": 47,
  "error": null
}
```

---

### 3.3 `GET /results/{session_id}`

Returns full `ExtractionResult` JSON object.

---

### 3.4 `GET /export/{session_id}`

Query params:
- `format`: `json` | `markdown`

Returns downloadable file with `Content-Disposition` header.

---

## 4. Scraping Specification

### 4.1 Playwright Scraping Flow

```
1. Launch headless Chromium
2. Navigate to X post URL
3. Wait for reply feed to load (aria: "timeline")
4. Repeatedly scroll and expand "show more replies" style controls until `max_comments` is reached or no new comments load
5. For each comment node:
   a. Extract tweet ID from data attributes
   b. Extract author info (username, display name, avatar, verified)
   c. Extract text content (preserve emojis, hashtags, mentions)
   d. Extract media attachments:
      - Images: src URL, alt text, width/height
      - Videos: m3u8/mp4 stream URL, duration, thumbnail
      - GIFs: video source URL, autoplay flag
      - Cards (link previews): og:title, og:image, canonical URL
      - Poll: options, vote counts (if public), end time
   e. Extract engagement counts (likes, retweets, replies, bookmarks)
   f. Extract timestamp (datetime attribute)
   g. Detect if it's a quote-tweet → recurse for quoted tweet
   h. Detect reply chain → recurse for replies
6. Expand t.co short-links via HEAD requests
7. Deduplicate by tweet ID
8. Return an ordered deduplicated list up to the requested limit
```

### 4.2 Anti-Bot Mitigation

- Random human-like scroll delays (1.5s – 3.5s)
- Randomized user-agent rotation
- Stealth plugin (`playwright-stealth`)
- Optional: Rotate through residential proxies (user-supplied)

---

## 5. LLM Integration Specification

### 5.1 Ollama Client

```python
# Endpoint: POST http://localhost:11434/api/chat
# Models: llama3, mistral, phi3, gemma2, qwen2

payload = {
    "model": "llama3",
    "messages": [
        {"role": "system", "content": ANNOTATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Annotate this comment:\n\n{comment.text}"}
    ],
    "stream": False,
    "format": "json"   # Structured JSON output
}
```

### 5.2 NVIDIA NIM Client

```python
# Endpoint: POST https://integrate.api.nvidia.com/v1/chat/completions
# Models: meta/llama-3.1-70b-instruct, mistralai/mixtral-8x22b-instruct-v0.1

headers = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "meta/llama-3.1-70b-instruct",
    "messages": [
        {"role": "system", "content": ANNOTATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Annotate this comment:\n\n{comment.text}"}
    ],
    "temperature": 0.2,
    "max_tokens": 300,
    "response_format": {"type": "json_object"}
}
```

### 5.3 Annotation Prompt

```
SYSTEM: You are a social media comment analyzer. Given a tweet/comment, return a JSON object with these exact keys:
{
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "sentiment_score": <float 0.0-1.0>,
  "topics": [<list of 1-5 short topic tags>],
  "summary": "<one sentence summary>",
  "language": "<ISO 639-1 code>",
  "is_spam": <true|false>
}
Return ONLY valid JSON. No markdown, no explanation.
```

---

## 6. Frontend Specification

### 6.1 Pages / Views

| View | Path | Description |
|---|---|---|
| Home | `/` | URL input form, backend selector, extract button |
| Results | `/results` | Comment cards grid/list view |
| Comment Detail | `/comment/:id` | Full expanded view of single comment |
| Export | `/export` | Download JSON or Markdown |

### 6.2 Comment Card Structure (UI)

```
┌───────────────────────────────────────────────────┐
│  Comment #1                          [Expand ▼]   │
├───────────────────────────────────────────────────┤
│  👤 @username · Display Name · ✓ Verified         │
│  🕐 Jan 15, 2025, 10:32 AM                        │
├───────────────────────────────────────────────────┤
│  💬 Comment Text                                   │
│  "Full text with #hashtags, @mentions, and emojis │
│   preserved as clickable links..."                 │
├───────────────────────────────────────────────────┤
│  📎 Resources (3)                                  │
│  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  🖼️ Image 1  │  │  🔗 https://example.com  │   │
│  │  [thumbnail] │  │  Title: "Page Title"      │   │
│  └──────────────┘  └──────────────────────────┘   │
│  🎥 Video: [thumbnail] · Duration: 0:32           │
├───────────────────────────────────────────────────┤
│  ❤️ 1.2K  🔁 340  💬 89  🔖 45                   │
├───────────────────────────────────────────────────┤
│  🤖 Sentiment: Positive (0.87)                     │
│  🏷️ Tags: AI, Technology, Opinion                  │
│  📝 "User expresses enthusiasm about AI progress"  │
└───────────────────────────────────────────────────┘
```

### 6.3 Resource Types — Visual Treatment

| Type | Icon | Display |
|---|---|---|
| Image | 🖼️ | Inline thumbnail, click → lightbox |
| Video | 🎥 | Thumbnail + play button overlay |
| GIF | 🎞️ | Auto-play preview |
| Link | 🔗 | OG preview card (title + thumbnail) |
| Quote Tweet | 🐦 | Embedded mini-card |
| Poll | 📊 | Bar chart with vote percentages |

---

## 7. Error Handling

| Error | HTTP Code | User Message |
|---|---|---|
| Invalid URL | 422 | "Please provide a valid X post URL" |
| Post not found / private | 404 | "Post is private or does not exist" |
| Rate limited by X | 429 | "Extraction rate-limited; try again in 60s" |
| LLM backend offline | 503 | "LLM backend unavailable; annotation disabled" |
| Timeout (scrape > 120s) | 504 | "Extraction timed out; try with fewer comments" |

---

## 8. Performance Requirements

| Metric | Target |
|---|---|
| Time to first comment card | < 5 seconds |
| 50 comments extracted | < 45 seconds |
| LLM annotation per comment | < 3 seconds (NVIDIA), < 8 seconds (Ollama) |
| UI renders 100 cards | < 500ms |
| Memory usage (backend) | < 512 MB |

---

## 9. Security Considerations

- Input URL validated against `x.com` / `twitter.com` domains only
- No credentials stored — NVIDIA API key stored in `.env`, never sent to frontend
- No scraped data persisted beyond session (in-memory by default)
- Optional: SQLite persistence for session history
- CORS restricted to `localhost` in development
