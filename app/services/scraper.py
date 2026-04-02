from __future__ import annotations

import html as html_module
import os
import re
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.config import Settings
from app.models.comment import Comment, CommentAuthor, CommentResource

def validate_x_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc.lower() not in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}:
        return False

    parts = [part for part in parsed.path.split("/") if part]
    return len(parts) >= 3 and parts[1].lower() == "status" and parts[2].isdigit()


def extract_status_id(url: str) -> str | None:
    if not validate_x_url(url):
        return None
    parts = [part for part in urlparse(url).path.split("/") if part]
    return parts[2] if len(parts) >= 3 else None


def parse_count(raw: str | None) -> int:
    if not raw:
        return 0
    text = raw.replace(",", "").strip().upper()
    multiplier = 1
    if text.endswith("K"):
        multiplier = 1_000
        text = text[:-1]
    elif text.endswith("M"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("B"):
        multiplier = 1_000_000_000
        text = text[:-1]
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return 0


class XScraper:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def extract_post_and_comments(
        self,
        url: str,
        max_comments: int,
        include_replies: bool,
        progress_callback: Callable[..., Awaitable[None]] | None = None,
    ) -> tuple[dict[str, Any], list[Comment]]:
        if not validate_x_url(url):
            raise ValueError("Please provide a valid X post URL")

        if progress_callback:
            await progress_callback(status="scraping", progress=5)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.settings.playwright_headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context_kwargs = {
                "user_agent": self.settings.user_agent,
                "locale": "en-US",
                "viewport": {"width": 1440, "height": 960},
                "device_scale_factor": 1,
                "is_mobile": False,
                "has_touch": False,
            }
            storage_state_path = Path(self.settings.x_storage_state_path)
            if storage_state_path.exists():
                context_kwargs["storage_state"] = str(storage_state_path)
            context = await browser.new_context(**context_kwargs)
            await context.add_init_script(STEALTH_INIT_SCRIPT)
            await self._apply_x_auth_cookies(context)
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.settings.scrape_timeout_ms)
                await page.wait_for_timeout(2500)
                await self._dismiss_popups(page)
                await page.wait_for_selector("article[data-testid='tweet']", timeout=15000)
                if progress_callback:
                    await progress_callback(status="scraping", progress=20)
                post, comments = await self._collect_thread(page, url, max_comments, include_replies)
                if progress_callback:
                    await progress_callback(status="scraping", progress=60, total_comments=len(comments))
                return post, comments[:max_comments]
            except PlaywrightTimeoutError as exc:
                raise RuntimeError("Post is private, unavailable, or X did not finish loading in time") from exc
            finally:
                await context.close()
                await browser.close()

    async def _dismiss_popups(self, page: Any) -> None:
        dismiss_texts = ["Not now", "Cancel", "Close"]
        for text in dismiss_texts:
            locator = page.get_by_text(text, exact=True)
            if await locator.count():
                try:
                    await locator.first.click(timeout=1000)
                    await page.wait_for_timeout(500)
                except Exception:
                    continue

    async def _collect_thread(
        self,
        page: Any,
        source_url: str,
        max_comments: int,
        include_replies: bool,
    ) -> tuple[dict[str, Any], list[Comment]]:
        unchanged_rounds = 0
        last_count = 0
        source_status_id = extract_status_id(source_url)
        post_payload: dict[str, Any] | None = None
        collected_payloads: dict[str, dict[str, Any]] = {}

        for _ in range(self.settings.scrape_max_scrolls):
            raw_articles = await page.locator("article[data-testid='tweet']").evaluate_all(EXTRACT_ARTICLES_SCRIPT)
            if raw_articles and post_payload is None:
                post_payload = raw_articles[0]

            for payload in raw_articles[1:]:
                comment_id = payload.get("comment_id") or ""
                if not comment_id or comment_id == source_status_id:
                    continue
                collected_payloads.setdefault(comment_id, payload)

            count = len(collected_payloads)
            if count >= max_comments:
                break
            if count == last_count:
                unchanged_rounds += 1
                if unchanged_rounds >= self.settings.scrape_idle_rounds:
                    break
            else:
                unchanged_rounds = 0
            last_count = count
            await self._expand_thread(page)
            await page.mouse.wheel(0, 2600)
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(self.settings.scrape_scroll_pause_ms)
        await self._expand_thread(page)

        if post_payload is None and await self._is_login_wall(page):
            raise RuntimeError(
                "X served a login wall for the replies. Configure an authenticated X session "
                "via playwright/storage_state.json or X_AUTH_TOKEN and X_CT0."
            )
        if post_payload is None:
            raise RuntimeError("No tweet articles were detected on the page")

        post = {
            "author": self._build_author(post_payload),
            "text": post_payload.get("text", ""),
            "timestamp": self._parse_timestamp(post_payload.get("timestamp")),
        }
        comments = [
            self._build_comment(payload, index=index, include_replies=include_replies)
            for index, payload in enumerate(collected_payloads.values(), start=1)
        ]
        return post, comments

    async def _expand_thread(self, page: Any) -> None:
        for label in EXPAND_THREAD_LABELS:
            locator = page.get_by_text(label, exact=False)
            try:
                count = await locator.count()
            except Exception:
                continue
            for index in range(min(count, 8)):
                try:
                    button = locator.nth(index)
                    if await button.is_visible():
                        await button.click(timeout=1200)
                        await page.wait_for_timeout(700)
                except Exception:
                    continue

    async def _apply_x_auth_cookies(self, context: Any) -> None:
        if not self.settings.x_auth_token or not self.settings.x_ct0:
            return

        cookies = [
            {
                "name": "auth_token",
                "value": self.settings.x_auth_token,
                "domain": ".x.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            },
            {
                "name": "ct0",
                "value": self.settings.x_ct0,
                "domain": ".x.com",
                "path": "/",
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax",
            },
        ]
        await context.add_cookies(cookies)

    async def _is_login_wall(self, page: Any) -> bool:
        try:
            body_text = await page.locator("body").inner_text()
        except Exception:
            return False
        markers = [
            "Don’t miss what’s happening",
            "People on X are the first to know.",
            "Read ",
            " replies",
        ]
        return all(marker in body_text for marker in markers)

    def _build_comment(self, payload: dict[str, Any], index: int, include_replies: bool) -> Comment:
        resources = [CommentResource.model_validate(item) for item in payload.get("resources", [])]
        raw_text = payload.get("text", "")
        hashtags = sorted({token for token in re.findall(r"#(\w+)", raw_text)})
        mentions = sorted({token for token in re.findall(r"@(\w+)", raw_text)})
        emails = sorted({m.lower() for m in _EMAIL_RE.findall(raw_text)})
        links = sorted({m for m in _URL_RE.findall(raw_text)})
        replies: list[Comment] = []
        if include_replies:
            for reply_payload in payload.get("replies", []):
                replies.append(self._build_comment(reply_payload, index=len(replies) + 1, include_replies=False))

        return Comment(
            index=index,
            comment_id=payload["comment_id"],
            author=self._build_author(payload),
            text=raw_text,
            text_html=_build_rich_html(raw_text),
            hashtags=hashtags,
            mentions=mentions,
            emails=emails,
            links=links,
            timestamp=self._parse_timestamp(payload.get("timestamp")),
            like_count=parse_count(payload.get("like_count")),
            retweet_count=parse_count(payload.get("retweet_count")),
            reply_count=parse_count(payload.get("reply_count")),
            bookmark_count=parse_count(payload.get("bookmark_count")),
            resources=resources,
            replies=replies,
        )

    @staticmethod
    def _build_author(payload: dict[str, Any]) -> CommentAuthor:
        return CommentAuthor(
            username=(payload.get("username") or "unknown").lstrip("@"),
            display_name=payload.get("display_name") or payload.get("username") or "Unknown",
            avatar_url=payload.get("avatar_url"),
            verified=bool(payload.get("verified")),
        )

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None


# ---------------------------------------------------------------------------
# Inline-entity regexes
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

_URL_RE = re.compile(
    r"https?://[^\s<>\"')\]]+",
    re.IGNORECASE,
)

# Combined pattern — order matters: URLs first (greedy), then emails, then
# hashtags, then @mentions, so email addresses aren't split at the @.
_INLINE_RE = re.compile(
    r"(https?://[^\s<>\"')\]]+)"              # group 1: URL
    r"|(\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b)"  # group 2: email
    r"|(#\w+)"                                # group 3: hashtag
    r"|(@\w+)",                               # group 4: @mention
    re.IGNORECASE,
)


def _build_rich_html(text: str) -> str:
    """Return an HTML string where @mentions, emails, hashtags and URLs are
    wrapped in styled, safe spans/anchors.  Plain text segments are
    HTML-escaped before insertion."""
    parts: list[str] = []
    cursor = 0
    for match in _INLINE_RE.finditer(text):
        # Escape the plain text that precedes this match
        parts.append(html_module.escape(text[cursor : match.start()]))
        raw = match.group(0)
        if match.group(1):  # URL
            safe_url = html_module.escape(raw, quote=True)
            parts.append(
                f'<a class="url-link" href="{safe_url}" target="_blank" rel="noreferrer">'
                f"{html_module.escape(raw)}</a>"
            )
        elif match.group(2):  # email
            parts.append(f'<span class="email">{html_module.escape(raw)}</span>')
        elif match.group(3):  # hashtag
            parts.append(f'<span class="hashtag">{html_module.escape(raw)}</span>')
        elif match.group(4):  # @mention
            username = html_module.escape(raw[1:], quote=True)  # strip leading @
            parts.append(
                f'<a class="mention" href="https://x.com/{username}" '
                f'target="_blank" rel="noreferrer">{html_module.escape(raw)}</a>'
            )
        cursor = match.end()
    parts.append(html_module.escape(text[cursor:]))
    return "".join(parts)


EXTRACT_ARTICLES_SCRIPT = """
(articles) => {
  const getText = (root, selectors) => {
    for (const selector of selectors) {
      const el = root.querySelector(selector);
      if (el && el.textContent) {
        return el.textContent.trim();
      }
    }
    return "";
  };

  const getMetric = (root, testId) => {
    const button = root.querySelector(`[data-testid="${testId}"]`);
    if (!button) return "0";
    const text = button.textContent || button.getAttribute("aria-label") || "0";
    const match = text.match(/([0-9.,]+\\s*[KMB]?)/i);
    return match ? match[1].replace(/\\s+/g, "") : "0";
  };

  const buildResources = (article) => {
    const resources = [];
    const push = (value) => {
      if (!value.url) return;
      if (resources.some((item) => item.type === value.type && item.url === value.url)) return;
      resources.push(value);
    };

    article.querySelectorAll('img').forEach((img) => {
      const src = img.getAttribute('src') || "";
      if (!src || src.includes('profile_images') || src.includes('emoji')) return;
      push({
        type: 'image',
        url: src,
        alt_text: img.getAttribute('alt') || "",
        thumbnail_url: src,
        metadata: {}
      });
    });

    article.querySelectorAll('video').forEach((video) => {
      const src = video.getAttribute('src') || video.querySelector('source')?.getAttribute('src') || "";
      if (!src) return;
      push({
        type: video.hasAttribute('loop') ? 'gif' : 'video',
        url: src,
        alt_text: null,
        thumbnail_url: video.getAttribute('poster') || null,
        metadata: {}
      });
    });

    article.querySelectorAll('a[href]').forEach((anchor) => {
      const href = anchor.href || "";
      if (!href) return;
      if (href.includes('/status/')) return;
      if (href.startsWith('https://t.co/') || href.startsWith('http://') || href.startsWith('https://')) {
        push({
          type: 'link',
          url: href,
          alt_text: null,
          thumbnail_url: null,
          metadata: { label: (anchor.textContent || '').trim() }
        });
      }
    });

    return resources;
  };

  const buildArticle = (article) => {
    const timeLink = article.querySelector('a[href*="/status/"]');
    const href = timeLink ? timeLink.getAttribute('href') || "" : "";
    const match = href.match(/\\/status\\/(\\d+)/);
    const commentId = match ? match[1] : "";
    const username = href.split('/').filter(Boolean)[0] || getText(article, ['div[data-testid="User-Name"] a[role="link"] span']);
    const textNode = article.querySelector('div[data-testid="tweetText"]');

    return {
      comment_id: commentId,
      username,
      display_name: getText(article, ['div[data-testid="User-Name"] > div:first-child span', 'div[data-testid="User-Name"] span']),
      avatar_url: article.querySelector('img[src*="profile_images"]')?.getAttribute('src') || null,
      verified: Boolean(article.querySelector('svg[aria-label*="Verified"]')),
      text: textNode ? textNode.innerText.trim() : "",
      text_html: textNode ? textNode.innerHTML : "",
      timestamp: article.querySelector('time')?.getAttribute('datetime') || null,
      like_count: getMetric(article, 'like'),
      retweet_count: getMetric(article, 'retweet'),
      reply_count: getMetric(article, 'reply'),
      bookmark_count: getMetric(article, 'bookmark'),
      resources: buildResources(article),
      replies: []
    };
  };

  return articles.map(buildArticle);
}
"""

EXPAND_THREAD_LABELS = [
    "Show more replies",
    "View more replies",
    "Show probable spam",
    "More replies",
]

STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
  get: () => undefined,
});
window.chrome = window.chrome || { runtime: {} };
Object.defineProperty(navigator, 'languages', {
  get: () => ['en-US', 'en'],
});
Object.defineProperty(navigator, 'plugins', {
  get: () => [1, 2, 3, 4, 5],
});
"""
