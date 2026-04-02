# X Comment Extractor

FastAPI app for extracting replies from a public X post, normalizing media and links, optionally annotating comments with NVIDIA, and exporting the result as JSON or Markdown.

## What It Does

- Accepts a public X or Twitter status URL
- Scrapes the post and visible replies with Playwright
- Extracts comment text, mentions, hashtags, emails, links, media URLs, and basic metrics
- Optionally annotates each top-level comment through NVIDIA's OpenAI-compatible API
- Serves a browser UI from `/` and export endpoints from the backend

The frontend source lives in `frontend/`, but the app serves it as a single bundled HTML response. `app/frontend.py` inlines `frontend/style.css` and `frontend/app.js` into `frontend/index.html` at request time, so there is no `/static` mount in the current build.

## Stack

- Backend: FastAPI, Pydantic, Uvicorn
- Scraping: Playwright
- HTTP: httpx
- Optional annotation: NVIDIA API via the OpenAI Python client
- Frontend: HTML, CSS, vanilla JavaScript

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Start the app:

```bash
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000`.

## Configuration

Copy `.env.example` to `.env` and set the values you need:

- `NVIDIA_API_KEY`: required only when `llm_annotate=true`
- `X_STORAGE_STATE_PATH`: path to a saved Playwright storage state for authenticated scraping
- `X_AUTH_TOKEN` and `X_CT0`: optional cookie-based X session
- `PLAYWRIGHT_HEADLESS`: set to `false` while debugging scraping behavior locally

## API

- `GET /`: bundled web UI
- `POST /extract`: start an extraction session
- `GET /status/{session_id}`: poll progress
- `GET /results/{session_id}`: fetch the structured result
- `GET /export/{session_id}?format=json|markdown`: download exported output

Example request:

```json
{
  "url": "https://x.com/openai/status/1234567890",
  "max_comments": 50,
  "include_replies": true,
  "llm_annotate": false,
  "llm_backend": "nvidia"
}
```

## Project Layout

```text
x-comment-extractor/
├── app/
│   ├── config.py
│   ├── frontend.py
│   ├── main.py
│   ├── models/
│   ├── routes/
│   └── services/
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── style.css
├── scripts/
├── tests/
├── .env.example
├── README.md
├── SCOPE.md
└── SPECIFICATION.md
```

## Testing

```bash
.venv/bin/pytest -q
```

## Current Boundaries

- Only the NVIDIA backend is implemented. Requests with another `llm_backend` return `422`.
- Results are stored in memory, so restarting the process clears sessions.
- Replies depend on what X exposes to Playwright. Login walls and DOM changes can reduce coverage.
- The scraper currently normalizes images, videos, GIFs, and outbound links. OG card enrichment, poll extraction, and quote-tweet parsing are not implemented in the current codebase.
