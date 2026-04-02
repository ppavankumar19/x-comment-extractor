# 🎯 SCOPE.md — X Post Comment Extractor Agent

**Version:** 1.0.0  
**Status:** Defined  
**Last Updated:** 2025  

---

## 1. Project Summary

Build an AI-powered web application that accepts a public X (Twitter) post URL and extracts comment threads with their complete content — text, images, videos, GIFs, links, polls, and quote-tweets — structured as numbered comment cards and optionally annotated by NVIDIA.

---

## 2. Goals

| # | Goal |
|---|---|
| G1 | Given any public X post URL, keep expanding and scrolling until the requested comment limit is reached or X stops yielding more visible comments |
| G2 | For each comment, capture all resource types: text, images, videos, GIFs, links, polls, quote-tweets |
| G3 | Present extracted data as structured, numbered comment cards in a web UI |
| G4 | Optionally annotate each comment (sentiment, topics, summary) via Ollama or NVIDIA NIM — both free |
| G5 | Allow export of all extracted data as JSON or Markdown |
| G6 | Run without requiring a paid subscription to any service |

---

## 3. In Scope

### 3.1 Core Extraction
- ✅ Public X / Twitter post URL parsing and validation
- ✅ Playwright-based headless scraping of comment threads
- ✅ Infinite scroll support (load all comments by auto-scrolling)
- ✅ Top-level comment extraction
- ✅ Nested reply thread extraction (configurable depth)
- ✅ Author profile: username, display name, avatar URL, verified status

### 3.2 Content Types Extracted Per Comment
- ✅ Full comment text (with emojis, Unicode, line breaks preserved)
- ✅ Hashtags (list)
- ✅ @Mentions (list)
- ✅ Images — direct CDN URL, alt text, dimensions
- ✅ Videos — stream URL or direct MP4, thumbnail, duration
- ✅ Animated GIFs — video source URL
- ✅ Embedded links — expanded URL (t.co → real URL), OG title, OG thumbnail
- ✅ Quote-tweets — minimal author + text + link of the quoted post
- ✅ Polls — options list, vote counts (when public), end time
- ✅ Engagement metrics — likes, retweets, replies, bookmarks

### 3.3 LLM Annotation (Optional)
- ✅ NVIDIA API integration (cloud free-tier; model: `nvidia/nemotron-3-super-120b-a12b`)
- ✅ Annotation is optional and off by default
- ✅ Per-comment annotation can add summary, topic tags, language detection, and spam flag

### 3.4 Web Application
- ✅ Single-page web UI (HTML + CSS + JS, no framework required)
- ✅ URL input form with requested comment limit
- ✅ Real-time progress indicator during extraction
- ✅ Numbered comment cards with expandable resource sections
- ✅ Image lightbox viewer
- ✅ Clickable, expanded links
- ✅ Filter bar (by sentiment, media type, keyword)
- ✅ Export button (JSON, Markdown)

### 3.5 Backend API
- ✅ FastAPI REST backend
- ✅ Background task queue for long extractions
- ✅ Status polling endpoint
- ✅ Session-based result storage (in-memory)
- ✅ Configurable via `.env` file

### 3.6 Developer Experience
- ✅ `.env.example` with all configuration options documented
- ✅ `requirements.txt` with pinned versions
- ✅ README with setup instructions for Windows, macOS, Linux
- ✅ Unit tests for scraper and LLM client modules

---

## 4. Out of Scope

| # | Item | Reason |
|---|---|---|
| OS1 | Private / locked X accounts | Requires login; scraping authenticated sessions is against ToS |
| OS2 | Downloading / saving video files to disk | Bandwidth/storage concerns; links are captured instead |
| OS3 | Real-time / live streaming extraction | Polling-based; no WebSocket stream from X |
| OS4 | Multi-platform support (YouTube, Reddit, Instagram) | Future phase; architecture designed for extensibility |
| OS5 | User accounts / login system | Single-user local app; no auth required |
| OS6 | Paid LLM APIs (OpenAI, Anthropic, etc.) | Project goal is zero-cost usage via NVIDIA free tier |
| OS7 | Twitter/X API v2 (Basic/Pro tier) | Paid; Playwright scraping used as primary method |
| OS8 | Mobile native app (iOS/Android) | Web-first; responsive design covers mobile browsers |
| OS9 | Persistent database (PostgreSQL/MySQL) | SQLite optional; in-memory default |
| OS10 | Automated scheduling / cron extraction | Manual trigger only in v1 |
| OS11 | Full audio transcription of videos | Out of scope for v1; possible v2 feature |

---

## 5. Assumptions

| # | Assumption |
|---|---|
| A1 | Target X posts are **public** (no authentication required) |
| A2 | User has Python 3.11+ installed |
| A3 | User has Playwright-compatible OS (Windows 10+, macOS 12+, Ubuntu 20.04+) |
| A4 | For Ollama backend: user has 8 GB+ RAM (for 7B models) or 16 GB+ (for 13B models) |
| A5 | For NVIDIA NIM: user has a valid (free) NVIDIA developer account |
| A6 | Internet connection is available for scraping and NVIDIA NIM (Ollama is offline) |
| A7 | X's DOM structure is scraped as-is; changes to X's HTML may require scraper updates |
| A8 | Videos are not downloaded; only stream/direct URLs are captured |

---

## 6. Constraints

| Constraint | Detail |
|---|---|
| **Zero paid services** | Ollama is free/local; NVIDIA NIM offers 1,000 free credits/month |
| **No X API paid tier** | All extraction via headless Playwright scraping |
| **Rate limiting** | X may throttle requests; built-in delays are mandatory |
| **Terms of Service** | User is responsible for complying with X's ToS for their use case |
| **Local compute** | Ollama requires a capable local machine; NVIDIA NIM offloads inference |

---

## 7. Phased Delivery

### Phase 1 — MVP (Week 1–2)
- [ ] FastAPI skeleton + `/extract` endpoint
- [ ] Playwright scraper for text + basic author info
- [ ] Simple web UI (URL input → raw JSON display)
- [ ] `.env` config system

### Phase 2 — Media & Resources (Week 3–4)
- [ ] Image, video, GIF extraction
- [ ] t.co link expansion
- [ ] OG preview card fetching
- [ ] Quote-tweet parsing
- [ ] Poll parsing

### Phase 3 — LLM Annotation (Week 5)
- [ ] Ollama client integration + annotation prompt
- [ ] NVIDIA NIM client integration
- [ ] Per-comment annotation pipeline
- [ ] Toggle in UI

### Phase 4 — Polished UI & Export (Week 6)
- [ ] Numbered comment cards with resource sections
- [ ] Image lightbox
- [ ] Filter bar
- [ ] JSON + Markdown export
- [ ] Progress indicator

### Phase 5 — Testing & Docs (Week 7)
- [ ] Unit tests for scraper + LLM client
- [ ] Error handling hardening
- [ ] Final README polish
- [ ] Video walkthrough / demo

---

## 8. Success Criteria

| Criterion | Measure |
|---|---|
| Extracts all visible comments | ≥ 95% of comments captured (vs manual count) |
| Resources correctly typed | Images, videos, links correctly categorized |
| LLM annotation works | Sentiment + topics returned for ≥ 90% of comments |
| No paid service required | Zero-cost setup verified on clean machine |
| Export works | JSON and Markdown files download correctly |
| Web UI usable | Non-technical user can extract in < 3 clicks |

---

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| X changes DOM structure | High | High | Modular scraper with CSS selector config file |
| X detects and blocks scraping | Medium | High | Random delays, stealth plugin, proxy support |
| NVIDIA NIM free credits exhausted | Low | Medium | Fall back to Ollama automatically |
| Ollama model too slow on weak hardware | Medium | Medium | Default to lightweight model (phi3 / gemma2:2b) |
| Videos not accessible without login | Low | Low | Capture URL only; document limitation |

---

## 10. Stakeholders

| Role | Responsibility |
|---|---|
| Developer | Builds and maintains the application |
| End User | Provides X URLs, reviews extracted comments |
| (Optional) Researcher | Uses export for analysis |

---

*This scope document defines what will and will not be built in v1.0. Any additions require a scope change review.*
