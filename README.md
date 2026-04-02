# 🐦 X Post Comment Extractor Agent

> An AI-powered agent that deeply extracts, analyzes, and structures every comment, reply, image, video, link, and media resource from any X (Twitter) post URL — presented in a clean, navigable web interface.

---

## 📌 Overview

The **X Post Comment Extractor Agent** takes a public X (Twitter) post URL and produces a richly structured, card-based breakdown of every comment thread beneath it. Each comment card exposes the author's profile, the raw text, embedded media (images, videos, GIFs), referenced links, quote-tweets, and reply chains — all analyzed and annotated by a local or cloud-hosted LLM.

The project runs entirely as a **web application** (FastAPI backend + HTML/JS frontend). The implemented build uses Playwright for scraping and NVIDIA for optional annotation:

| Capability | Provider | Cost |
|---|---|---|
| **Comment extraction** | Playwright + public/authenticated X session | Free |
| **Optional annotation** | NVIDIA API | Free-tier available |

---

## ✨ Features

- 🔗 **Paste any public X post URL** and extract all top-level comments + nested replies
- 🖼️ **Media extraction** — images, videos, GIFs, and card thumbnails per comment
- 🔤 **Full text extraction** — hashtags, mentions, emojis preserved
- 🔗 **Link resolution** — expands t.co short-links to real URLs
- 🤖 **Optional LLM annotation** — topic tags and summary per comment via NVIDIA
- 🗂️ **Structured comment cards** — Comment #N → Author → Text → Resources (media / links)
- 📤 **Export** to JSON or Markdown
- 🌐 **Web UI** — no CLI knowledge required

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, Tailwind CSS, Vanilla JS (or optionally React) |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **Scraping** | Playwright (headless Chromium), Tweepy (Twitter API v2 optional) |
| **LLM — Cloud** | NVIDIA API (`nvidia/nemotron-3-super-120b-a12b`) |
| **Data** | Pydantic models, JSON |
| **Export** | JSON, Markdown |

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.11+
python --version

# Node.js (optional, for React frontend)
node --version

# Playwright browsers
pip install playwright
playwright install chromium

```

### 2. Clone & Install

```bash
git clone https://github.com/yourname/x-comment-extractor.git
cd x-comment-extractor

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
# LLM backend
LLM_BACKEND=nvidia

# NVIDIA annotation backend
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
X_STORAGE_STATE_PATH=playwright/storage_state.json
X_AUTH_TOKEN=
X_CT0=

# Annotation is optional and disabled by default in the UI
```

### 4. Run

```bash
uvicorn app.main:app --reload --port 8000
```

Open your browser at `http://localhost:8000`

---

## 🔑 Getting Free API Keys

### NVIDIA API
1. Go to [build.nvidia.com](https://build.nvidia.com)
2. Sign up / Log in
3. Navigate to **API Keys** → **Generate Key**
4. Use the key in `.env`

---

## 📁 Project Structure

```
x-comment-extractor/
├── app/
│   ├── main.py                # FastAPI app entry point
│   ├── routes/
│   │   ├── extract.py         # POST /extract endpoint
│   │   └── export.py          # GET /export endpoint
│   ├── services/
│   │   ├── scraper.py         # Playwright-based X scraper
│   │   ├── media_parser.py    # Image/video/link extractor
│   │   ├── llm_client.py      # NVIDIA client
│   │   └── annotator.py       # LLM annotation logic
│   ├── models/
│   │   └── comment.py         # Pydantic data models
│   └── config.py              # Settings from .env
├── frontend/
│   ├── index.html             # Main web UI
│   ├── style.css
│   └── app.js
├── tests/
│   ├── test_scraper.py
│   └── test_llm_client.py
├── .env.example
├── requirements.txt
├── README.md
├── SPECIFICATION.md
└── SCOPE.md
```

---

## 🖥️ Usage — Web UI

1. Open `http://localhost:8000`
2. Paste an X post URL (e.g., `https://x.com/elonmusk/status/123456789`)
3. If X hides replies behind a login wall, provide an authenticated X session via `playwright/storage_state.json` or `X_AUTH_TOKEN` + `X_CT0`
4. Click **Extract Comments**
5. Browse structured comment cards:

```
┌─────────────────────────────────────────┐
│ Comment #1                              │
│ 👤 @username · John Doe                 │
│ ─────────────────────────────────────── │
│ 💬 "This is the comment text with       │
│     #hashtags and @mentions"            │
│ ─────────────────────────────────────── │
│ 📎 Resources                            │
│   🖼️ image1.jpg                         │
│   🎥 video.mp4                          │
│   🔗 https://example.com               │
│ ─────────────────────────────────────── │
│ 🤖 Sentiment: Positive | Tags: AI, Tech │
└─────────────────────────────────────────┘
```

---

## 📤 Export

```bash
# JSON
GET /export?format=json&session_id=<id>

# Markdown
GET /export?format=markdown&session_id=<id>
```

---

## ⚠️ Limitations & Notes

- **Public X posts may still hide replies when unauthenticated**; use an authenticated saved session or X cookies for deeper extraction
- X's rate limiting and bot detection may throttle requests; add delays between requests
- The Twitter/X API v2 free tier has restricted endpoints — Playwright scraping is used as the primary method
- LLM annotation is optional and off by default in the UI
- Videos are linked/referenced, not downloaded, by default

---

## 🤝 Contributing

Pull requests are welcome. Please open an issue first for major changes.

---

## 📄 License

MIT License © 2025
