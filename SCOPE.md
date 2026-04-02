# Scope

**Status:** current implemented scope  
**Last Updated:** 2026-04-02

## In Scope

- Local FastAPI web app for extracting public X post replies
- Browser UI served from `/`
- Playwright-based scraping of the main post and visible comments
- Extraction of:
  - author metadata
  - raw text
  - rendered `text_html`
  - mentions, hashtags, emails, and links
  - image, video, GIF, and outbound link resources
  - basic engagement counts
  - first-level nested replies when requested
- Optional NVIDIA-powered per-comment annotation
- JSON and Markdown export
- In-memory session tracking with progress polling

## Out of Scope

- X API integration
- Persistent database storage
- User accounts or multi-user auth
- Non-NVIDIA LLM backends
- Static asset serving from `/static`
- OG preview scraping
- poll extraction
- quote-tweet parsing
- media downloads to disk
- scheduled or recurring extraction jobs

## Assumptions

- Target URLs are public X or Twitter status pages.
- Users run the app locally with Python 3.11+ and Playwright Chromium installed.
- Some posts or replies may require an authenticated X session for reliable scraping.
- The DOM structure exposed by X can change and may require scraper updates.

## Operational Limits

- Session data is lost when the process restarts.
- Annotation requires a valid `NVIDIA_API_KEY`.
- Login walls, throttling, or anti-bot changes on X can reduce extraction coverage.

## Done Criteria For This Repo

- Start extraction through `POST /extract`
- Poll progress with `GET /status/{session_id}`
- Retrieve results through `GET /results/{session_id}`
- Export JSON or Markdown from `GET /export/{session_id}`
- Pass the current unit test suite
