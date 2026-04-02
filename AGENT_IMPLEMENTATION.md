# Agent Implementation Notes

**Status:** design draft only, not implemented in this repository  
**Last Updated:** 2026-04-02

## Current State

The repository ships a form-driven FastAPI web app. It does not currently expose an autonomous agent loop, chat endpoint, or tool-calling runtime.

## Reusable Building Blocks

An agent layer could reuse the existing services directly:

- URL validation from [app/services/scraper.py](/home/pavankumar19/x-comment-extractor/app/services/scraper.py)
- extraction orchestration from [app/services/extraction.py](/home/pavankumar19/x-comment-extractor/app/services/extraction.py)
- session lifecycle from [app/services/session_store.py](/home/pavankumar19/x-comment-extractor/app/services/session_store.py)
- export helpers from [app/services/exporter.py](/home/pavankumar19/x-comment-extractor/app/services/exporter.py)

## Minimal Agent Surface

If an agent layer is added later, the practical tool surface is:

1. `validate_url(url)`
2. `extract_comments(url, max_comments, include_replies, llm_annotate)`
3. `get_status(session_id)`
4. `get_results(session_id)`
5. `export_results(session_id, format)`

## Recommended Approach

- Keep the FastAPI extraction services as the source of truth.
- Add a thin agent adapter instead of duplicating scraping or export logic.
- Treat annotation as optional and preserve the current NVIDIA-only constraint unless another backend is implemented in code.
